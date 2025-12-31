from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from datetime import datetime
from django.db import connection
from django.utils import timezone
import io
import base64
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')


from apps.manager.models import recipes_model, employees_model, orders_items_model

def _top_sellers():
    """
    Return a short list of top-selling recipes from today's order items.
    
    Executes a raw SQL query to aggregate recipe orders from today,
    joining the recipe_orders and orders tables. The recipe_orders table
    has no explicit primary key, requiring raw SQL for aggregation.
    
    Returns:
        list[dict]: List of up to 5 dictionaries containing:
            - name (str): Recipe name or fallback "Recipe {id}"
            - count (int): Total number of times ordered today
            
    Note:
        Results are ordered by count in descending order (best sellers first).
        Uses timezone-aware datetime for accurate date filtering.
    """
    today = timezone.localdate()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT ro.recipe_id, COUNT(*) AS total
            FROM recipe_orders ro
            JOIN orders o ON o.id = ro.order_id
            WHERE o.time BETWEEN %s AND %s
            GROUP BY ro.recipe_id
            ORDER BY total DESC
            LIMIT 5
            """,
            [start, end],
        )
        rows = cursor.fetchall()
    recipe_ids = [r[0] for r in rows]
    names = {r.id: r.name for r in recipes_model.Recipe.objects.filter(id__in=recipe_ids)}
    return [
        {"name": names.get(recipe_id, f"Recipe {recipe_id}"), "count": total}
        for recipe_id, total in rows
    ]


def _low_stock(threshold_buffer=5):
    """
    Return inventory items at or near minimum stock levels.
    
    Scans all inventory items and identifies those with quantities at or below
    their minimum stock level plus a threshold buffer. Items without a defined
    minimum stock are excluded from results.
    
    Args:
        threshold_buffer (int, optional): Additional units above minimum_stock
            to consider as "low stock". Defaults to 5.
    
    Returns:
        list[dict]: List of up to 6 dictionaries containing:
            - ingredient (str): Ingredient name
            - quantity (float): Current quantity in stock
            - minimum (int): Minimum stock threshold
            
    Note:
        Results are limited to the first 6 items found.
        Items with minimum_stock=None are skipped.
    """
    lows = []
    for item in recipes_model.Inventory.objects.all():
        if item.minimum_stock is None:
            continue
        if item.quantity <= item.minimum_stock + threshold_buffer:
            lows.append({
                "ingredient": item.ingredient,
                "quantity": item.quantity,
                "minimum": item.minimum_stock,
            })
    return lows[:6]

def home(request):
    """
    Render the manager console home page with dashboard data.
    
    Displays all inventory items, top sellers for today, and low stock alerts.
    Supports tab navigation via URL parameter.
    
    Args:
        request (HttpRequest): Django request object containing:
            - GET params:
                - tab (str, optional): Active tab identifier, defaults to 'home'
    
    Returns:
        HttpResponse: Rendered HTML template with context containing:
            - ingredients (QuerySet): All inventory items
            - top_sellers (list): Top 5 selling recipes today
            - low_stock (list): Up to 6 low stock items
            - active_tab (str): Current active tab identifier
            
    Template:
        manager/home.html
    """
    ingredients = recipes_model.Inventory.objects.all()
    active_tab = request.GET.get('tab', 'home')  # Get tab from URL parameter
    context = {
        "ingredients": ingredients,
        "top_sellers": _top_sellers(),
        "low_stock": _low_stock(),
        "active_tab": active_tab,  # Pass to template
    }
    return render(request, "manager/home.html", context)

# ------------------- TAB VIEW -------------------
def tab_view(request, tab):
    """
    Serve partial HTML content for specific tabs in the manager console.
    
    Routes to different templates based on the tab parameter, providing
    appropriate context data for each tab view. Supports dynamic tab loading
    without full page refresh.
    
    Args:
        request (HttpRequest): Django request object
        tab (str): Tab identifier, one of:
            - 'menuManage': Menu management interface
            - 'reports': Reports interface
            - 'employees': Employee management interface
            - 'inventory': Inventory management interface
            - Other values default to home tab
    
    Returns:
        HttpResponse: Rendered partial HTML template with tab-specific context:
            - menuManage: ingredients, recipes, delete_errors
            - reports: No additional context
            - employees: employees list
            - inventory: ingredients list
            - home (default): ingredients, top_sellers, low_stock
            
    Templates:
        - manager/menuManage.html
        - manager/reports.html
        - manager/employees.html
        - manager/inventory.html
        - manager/home.html (default)
    """
    if tab == "menuManage":
        ingredients = recipes_model.Inventory.objects.all()
        recipes = recipes_model.Recipe.objects.all()
        delete_errors = []

        return render(request, "manager/menuManage.html", {
            "ingredients": ingredients,
            "recipes": recipes,
            "delete_errors": delete_errors,
        })

    elif tab == "reports":
        return render(request, "manager/reports.html")
    elif tab == "employees":
        employees = employees_model.Employee.objects.all()
        return render(request, "manager/employees.html", {"employees": employees})
    elif tab == "inventory":
        ingredients = recipes_model.Inventory.objects.all()
        return render(request, "manager/inventory.html", {"ingredients": ingredients})
    else:
        # Home tab
        context = {
            "ingredients": recipes_model.Inventory.objects.all(),
            "top_sellers": _top_sellers(),
            "low_stock": _low_stock(),
        }
        return render(request, "manager/home.html", context)
# ------------------- ADD ITEM --------------------
@csrf_exempt
def add_item(request):
    """
    Create a new menu item (recipe) with associated ingredients.
    
    Validates input data, checks for duplicate names (case-insensitive), and
    creates both the recipe and its ingredient relationships. CSRF exempt for
    AJAX compatibility.
    
    Args:
        request (HttpRequest): POST request containing:
            - name (str): Recipe name
            - type (str): Recipe type/category
            - price (str): Recipe price as string
            - active (str): "true" for active, other for inactive
            - ingredients (list[str]): List of ingredient IDs
    
    Returns:
        JsonResponse: Success or error response
            Success (200):
                - success (bool): True
                - message (str): Confirmation message
                - recipe (dict): Created recipe data with id, name, type, price,
                  active status, ingredient_ids, and ingredient_names
            Error (200):
                - success (bool): False
                - errors (list[str]): Validation error messages
                - error (str): Exception message if applicable
    
    Validation:
        - Name, type, and price are required
        - At least one ingredient must be selected
        - Recipe name must be unique (case-insensitive)
        
    Side Effects:
        - Creates Recipe object
        - Creates RecipeIngredient relationships
    """
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        recipe_type = request.POST.get("type", "").strip()
        price = request.POST.get("price", "").strip()
        active = request.POST.get("active") == "true"
        ingredient_ids = request.POST.getlist("ingredients")

        errors = []
        if not name:
            errors.append("Name is required.")
        if not recipe_type:
            errors.append("Type is required.")
        if not price:
            errors.append("Price is required.")
        if len(ingredient_ids) == 0:
            errors.append("At least one ingredient must be selected.")

        # Check for duplicate name (case-insensitive)
        if recipes_model.Recipe.objects.filter(name__iexact=name).exists():
            errors.append(f"A menu item with the name '{name}' already exists.")

        if errors:
            return JsonResponse({"success": False, "errors": errors})

        try:
            new_recipe = recipes_model.Recipe.objects.create(
                name=name,
                type=recipe_type,
                price=price,
                active=active
            )

            for ing_id in ingredient_ids:
                ri = recipes_model.RecipeIngredient(
                    recipe_id=new_recipe.id,
                    ingredient_id=ing_id
                )
                ri.save()

            # Get ingredient names for display
            ingredients = recipes_model.Inventory.objects.filter(id__in=ingredient_ids)
            ingredient_names = [ing.ingredient for ing in ingredients]

            return JsonResponse({
                "success": True,
                "message": f"{name} added successfully!",
                "recipe": {
                    "id": new_recipe.id,
                    "name": new_recipe.name,
                    "type": new_recipe.type,
                    "price": float(new_recipe.price),
                    "active": new_recipe.active,
                    "ingredient_ids": ingredient_ids,
                    "ingredient_names": ingredient_names
                }
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})


# ------------------- EDIT ITEM  -------------------
@csrf_exempt
def edit_item(request):
    """
    Update an existing menu item (recipe) and its ingredients.
    
    Validates input, checks for name conflicts with other recipes, and updates
    both the recipe and its ingredient relationships. Existing ingredient
    relationships are deleted and recreated.
    
    Args:
        request (HttpRequest): POST request containing:
            - recipe_id (str): ID of recipe to update
            - name (str): Updated recipe name
            - type (str): Updated recipe type/category
            - price (str): Updated price as string
            - active (str): "true" for active, other for inactive
            - ingredients (list[str]): List of ingredient IDs
    
    Returns:
        JsonResponse: Success or error response
            Success (200):
                - success (bool): True
                - message (str): Confirmation message
                - recipe (dict): Updated recipe data with id, name, type, price,
                  active status, ingredient_ids, and ingredient_names
            Error (200):
                - success (bool): False
                - errors (list[str]): Validation error messages
                - error (str): Exception or "No recipe selected" message
    
    Validation:
        - recipe_id is required
        - Name, type, and price are required
        - At least one ingredient must be selected
        - Recipe name must be unique except for current recipe (case-insensitive)
        
    Side Effects:
        - Updates Recipe object
        - Deletes all existing RecipeIngredient relationships
        - Creates new RecipeIngredient relationships
    """
    if request.method == "POST":
        recipe_id = request.POST.get("recipe_id")
        name = request.POST.get("name", "").strip()
        recipe_type = request.POST.get("type", "").strip()
        price = request.POST.get("price", "").strip()
        active = request.POST.get("active") == "true"
        ingredient_ids = request.POST.getlist("ingredients")

        if not recipe_id:
            return JsonResponse({"success": False, "error": "No recipe selected."})

        errors = []
        if not name:
            errors.append("Name is required.")
        if not recipe_type:
            errors.append("Type is required.")
        if not price:
            errors.append("Price is required.")
        if len(ingredient_ids) == 0:
            errors.append("At least one ingredient must be selected.")

        # Check for duplicate name (case-insensitive), excluding the current recipe
        duplicate = recipes_model.Recipe.objects.filter(name__iexact=name).exclude(id=recipe_id).first()
        if duplicate:
            errors.append(f"A menu item with the name '{name}' already exists.")

        if errors:
            return JsonResponse({"success": False, "errors": errors})

        try:
            recipe = get_object_or_404(recipes_model.Recipe, id=recipe_id)
            recipe.name = name
            recipe.type = recipe_type
            recipe.price = price
            recipe.active = active
            recipe.save()

            recipes_model.RecipeIngredient.objects.filter(recipe_id=recipe_id).delete()
            for ing_id in ingredient_ids:
                ri = recipes_model.RecipeIngredient(recipe_id=recipe_id, ingredient_id=ing_id)
                ri.save()

            # Get ingredient names for display
            ingredients = recipes_model.Inventory.objects.filter(id__in=ingredient_ids)
            ingredient_names = [ing.ingredient for ing in ingredients]

            return JsonResponse({
                "success": True,
                "message": f"{name} updated successfully!",
                "recipe": {
                    "id": recipe.id,
                    "name": recipe.name,
                    "type": recipe.type,
                    "price": float(recipe.price),
                    "active": recipe.active,
                    "ingredient_ids": ingredient_ids,
                    "ingredient_names": ingredient_names
                }
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})


# ------------------- DELETE ITEM -------------------
@csrf_exempt
def delete_item(request):
    """
    Delete a menu item (recipe) and all its ingredient relationships.
    
    Removes both the recipe record and all associated RecipeIngredient entries.
    Cascading deletion ensures no orphaned relationships remain.
    
    Args:
        request (HttpRequest): POST request containing:
            - recipe_id (str): ID of recipe to delete
    
    Returns:
        JsonResponse: Success or error response
            Success (200):
                - success (bool): True
                - message (str): Confirmation with recipe name
            Error (200):
                - success (bool): False
                - error (str): Error message ("No recipe selected", exception message,
                  or "Invalid request method")
    
    Side Effects:
        - Deletes all RecipeIngredient records for the recipe
        - Deletes the Recipe record
        
    Note:
        Does not validate if recipe is currently used in pending orders.
        Consider adding such validation before deployment.
    """
    if request.method == "POST":
        recipe_id = request.POST.get("recipe_id")
        
        if not recipe_id:
            return JsonResponse({"success": False, "error": "No recipe selected."})

        try:
            recipe = get_object_or_404(recipes_model.Recipe, id=recipe_id)
            recipe_name = recipe.name
            
            recipes_model.RecipeIngredient.objects.filter(recipe_id=recipe_id).delete()
            recipes_model.Recipe.objects.filter(id=recipe_id).delete()
            
            return JsonResponse({
                "success": True,
                "message": f"{recipe_name} deleted successfully."
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})


# ------------------- GET RECIPE  -------------------
def get_recipe(request, recipe_id):
    """
    Retrieve recipe data in JSON format for editing purposes.
    
    Fetches recipe details and associated ingredient IDs, formatted for
    populating edit forms in the frontend.
    
    Args:
        request (HttpRequest): Django request object
        recipe_id (int/str): ID of recipe to retrieve
    
    Returns:
        JsonResponse: Recipe data or error
            Success (200):
                - id (int): Recipe ID
                - name (str): Recipe name
                - type (str): Recipe type/category
                - price (float): Recipe price
                - active (bool): Active status
                - ingredient_ids (list[str]): List of ingredient IDs as strings
            Error (404): Recipe not found
                - error (str): "Recipe not found"
            Error (500): Server error
                - error (str): Exception message
    
    Note:
        Ingredient IDs are returned as strings for compatibility with
        frontend form select elements that use string values.
    """
    try:
        recipe = get_object_or_404(recipes_model.Recipe, id=recipe_id)
        
        ingredients = recipes_model.RecipeIngredient.objects.filter(
            recipe_id=recipe_id
        ).values('ingredient_id')
        
        ingredient_ids = [str(ing['ingredient_id']) for ing in ingredients]

        data = {
            "id": recipe.id,
            "name": recipe.name,
            "type": recipe.type,
            "price": float(recipe.price),
            "active": recipe.active,
            "ingredient_ids": ingredient_ids
        }
        
        return JsonResponse(data)
    
    except recipes_model.Recipe.DoesNotExist:
        return JsonResponse({"error": "Recipe not found"}, status=404)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
# ------------------- ADD EMPLOYEE -------------------
@csrf_exempt
def add_employee(request):
    """
    Create a new employee record with validation.
    
    Validates employee data including date formats and creates a new employee
    record. Date fields are optional but must be valid YYYY-MM-DD format if provided.
    
    Args:
        request (HttpRequest): POST request containing:
            - name (str): Employee name
            - role (str): Employee role/position
            - date_of_birth (str, optional): DOB in YYYY-MM-DD format
            - date_of_hire (str, optional): Hire date in YYYY-MM-DD format
            - password (str): Employee password
    
    Returns:
        JsonResponse: Success or error response
            Success (200):
                - success (bool): True
                - message (str): Confirmation message
                - employee (dict): Created employee with id, name, role,
                  date_of_birth, and date_of_hire (dates as YYYY-MM-DD strings)
            Error (200):
                - success (bool): False
                - errors (list[str]): Validation error messages
    
    Validation:
        - Name and role are required
        - Date strings must be in YYYY-MM-DD format if provided
        - Invalid dates generate specific error messages
        
    Side Effects:
        - Creates Employee object with plain text password
        
    Security Note:
        Password is stored in plain text. Consider implementing proper
        password hashing (e.g., Django's make_password) before production use.
    """
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        role = request.POST.get("role", "").strip()
        dob_str = request.POST.get("date_of_birth", "").strip()
        doh_str = request.POST.get("date_of_hire", "").strip()
        password = request.POST.get("password", "").strip()

        errors = []
        if not name:
            errors.append("Name is required.")
        if not role:
            errors.append("Role is required.")

        dob = None
        doh = None
        try:
            if dob_str:
                dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Invalid Date of Birth format. Use YYYY-MM-DD.")
        try:
            if doh_str:
                doh = datetime.strptime(doh_str, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Invalid Date of Hire format. Use YYYY-MM-DD.")

        if errors:
            return JsonResponse({"success": False, "errors": errors})

        new_employee = employees_model.Employee.objects.create(
            name=name,
            role=role,
            date_of_birth=dob,
            date_of_hire=doh,
            password=password
        )

        return JsonResponse({
            "success": True,
            "message": f"{name} added successfully!",
            "employee": {
                "id": new_employee.id,
                "name": new_employee.name,
                "role": new_employee.role,
                "date_of_birth": new_employee.date_of_birth.strftime("%Y-%m-%d") if new_employee.date_of_birth else "",
                "date_of_hire": new_employee.date_of_hire.strftime("%Y-%m-%d") if new_employee.date_of_hire else ""
            }
        })

    return JsonResponse({"success": False, "error": "Invalid request method."})


# ------------------- UPDATE EMPLOYEE  -------------------
@csrf_exempt
def update_employee(request):
    """
    Update an existing employee's information.
    
    Modifies employee details including name, role, and date fields. Dates
    must be in YYYY-MM-DD format if provided. Password is not updated by this function.
    
    Args:
        request (HttpRequest): POST request containing:
            - employee_id (str): ID of employee to update
            - name (str): Updated employee name
            - date_of_birth (str, optional): Updated DOB in YYYY-MM-DD format
            - role (str): Updated role/position
            - date_of_hire (str, optional): Updated hire date in YYYY-MM-DD format
    
    Returns:
        JsonResponse: Success or error response
            Success (200):
                - success (bool): True
                - message (str): "Employee updated successfully."
                - employee (dict): Updated employee with id, name, role,
                  date_of_birth, and date_of_hire (dates as YYYY-MM-DD strings)
            Error (200):
                - success (bool): False
                - errors (list[str]): Validation error messages
                - error (str): "No employee selected" or "Employee not found"
    
    Validation:
        - employee_id is required
        - Name and role are required
        - Date strings must be in YYYY-MM-DD format if provided
        
    Side Effects:
        - Updates Employee object fields
        
    Note:
        Password field is intentionally not updated here. Use reset_password()
        for password changes.
    """
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        name = request.POST.get("name", "").strip()
        date_of_birth = request.POST.get("date_of_birth", "").strip()
        role = request.POST.get("role", "").strip()
        date_of_hire = request.POST.get("date_of_hire", "").strip()

        if not employee_id:
            return JsonResponse({"success": False, "error": "No employee selected."})

        try:
            employee = get_object_or_404(employees_model.Employee, id=employee_id)
        except:
            return JsonResponse({"success": False, "error": "Employee not found."})

        errors = []
        if not name:
            errors.append("Name is required.")
        if not role:
            errors.append("Role is required.")

        dob = None
        doh = None
        try:
            if date_of_birth:
                dob = datetime.strptime(date_of_birth, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Invalid Date of Birth format. Use YYYY-MM-DD.")
        try:
            if date_of_hire:
                doh = datetime.strptime(date_of_hire, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Invalid Date of Hire format. Use YYYY-MM-DD.")

        if errors:
            return JsonResponse({"success": False, "errors": errors})

        employee.name = name
        employee.role = role
        employee.date_of_birth = dob
        employee.date_of_hire = doh
        employee.save()

        return JsonResponse({
            "success": True,
            "message": "Employee updated successfully.",
            "employee": {
                "id": employee.id,
                "name": employee.name,
                "role": employee.role,
                "date_of_birth": employee.date_of_birth.strftime("%Y-%m-%d") if employee.date_of_birth else "",
                "date_of_hire": employee.date_of_hire.strftime("%Y-%m-%d") if employee.date_of_hire else ""
            }
        })

    return JsonResponse({"success": False, "error": "Invalid request method."})


# ------------------- RESET PASSWORD  -------------------
@csrf_exempt
def reset_password(request):
    """
    Reset an employee's password to a new value.
    
    Updates the employee's password field. Separated from general employee
    updates for security and audit purposes.
    
    Args:
        request (HttpRequest): POST request containing:
            - employee_id (str): ID of employee whose password to reset
            - new_password (str): New password value
    
    Returns:
        JsonResponse: Success or error response
            Success (200):
                - success (bool): True
                - message (str): Confirmation with employee name
            Error (200):
                - success (bool): False
                - error (str): Error message ("No employee selected",
                  "Password is required", or "Employee not found")
    
    Validation:
        - employee_id is required
        - new_password is required and cannot be empty
        
    Side Effects:
        - Updates Employee.password field
        
    Security Warning:
        Password is stored in plain text. Implement proper password hashing
        (Django's make_password/set_password) before production deployment.
        Consider adding password strength requirements and confirmation.
    """
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")
        new_password = request.POST.get("new_password", "").strip()

        if not employee_id:
            return JsonResponse({"success": False, "error": "No employee selected."})
        
        if not new_password:
            return JsonResponse({"success": False, "error": "Password is required."})

        try:
            employee = get_object_or_404(employees_model.Employee, id=employee_id)
        except:
            return JsonResponse({"success": False, "error": "Employee not found."})

        employee.password = new_password
        employee.save()

        return JsonResponse({
            "success": True,
            "message": f"Password reset successfully for {employee.name}."
        })

    return JsonResponse({"success": False, "error": "Invalid request method."})


# ------------------- DELETE EMPLOYEE  -------------------
@csrf_exempt
def delete_employee(request):
    """
    Delete an employee record from the database.
    
    Permanently removes the employee record. Does not check for foreign key
    constraints or associated records (e.g., orders placed by this employee).
    
    Args:
        request (HttpRequest): POST request containing:
            - employee_id (str): ID of employee to delete
    
    Returns:
        JsonResponse: Success or error response
            Success (200):
                - success (bool): True
                - message (str): Confirmation with employee name
            Error (200):
                - success (bool): False
                - error (str): Error message ("No employee selected",
                  exception message, or "Invalid request method")
    
    Side Effects:
        - Deletes Employee record
        
    Warning:
        No confirmation dialog or soft delete. Consider implementing:
        - Soft delete (is_active flag) instead of hard delete
        - Validation for employees with associated orders
        - Audit trail of deletions
        - Admin-only permission check
    """
    if request.method == "POST":
        employee_id = request.POST.get("employee_id")

        if not employee_id:
            return JsonResponse({"success": False, "error": "No employee selected."})

        try:
            employee = get_object_or_404(employees_model.Employee, id=employee_id)
            employee_name = employee.name
            employee.delete()
            return JsonResponse({
                "success": True,
                "message": f"{employee_name} deleted successfully."
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})

# ------------------- PRODUCT USAGE REPORT -------------------
@require_GET
def product_usage_report(request):
    """
    Generate a report of ingredient usage within a date range.
    
    Executes raw SQL to join orders, recipe_orders, recipe_ingredient, and
    inventory tables, aggregating ingredient usage counts for all orders
    within the specified time period.
    
    Args:
        request (HttpRequest): GET request with query parameters:
            - start_date (str): Start datetime in ISO format (YYYY-MM-DDTHH:MM)
            - end_date (str): End datetime in ISO format (YYYY-MM-DDTHH:MM)
    
    Returns:
        JsonResponse: Array of ingredient usage data or error
            Success (200): List of dictionaries containing:
                - name (str): Ingredient name
                - used_quantity (int): Total times used in recipes
                - price (float): Current price per unit
                Ordered by used_quantity descending (most used first)
            Error (400): Missing or invalid parameters
                - error (str): Description of parameter issue
            Error (500): Database error
                - error (str): Database error description
    
    Validation:
        - Both start_date and end_date are required
        - Dates must be valid ISO format (YYYY-MM-DDTHH:MM)
        - start_date must be before or equal to end_date
        
    Note:
        Returns empty array if no orders found in date range.
        Used_quantity represents number of times ingredient appeared in
        ordered recipes, not actual quantity consumed (which would require
        per-recipe ingredient amounts).
    """
    start_str = request.GET.get("start_date")
    end_str = request.GET.get("end_date")

    if not start_str or not end_str:
        return JsonResponse({"error": "Missing start_date or end_date"}, status=400)

    try:
        start_dt = datetime.fromisoformat(start_str)
        end_dt = datetime.fromisoformat(end_str)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid date format. Use YYYY-MM-DDTHH:MM"}, status=400)

    if start_dt > end_dt:
        return JsonResponse({"error": "Start date must be before end date"}, status=400)

    # Use raw SQL query (like Java version) to join tables and aggregate
    query = """
        SELECT i.ingredient, COUNT(*) as used_quantity, i.price
        FROM orders o
        JOIN recipe_orders ro ON o.id = ro.order_id
        JOIN recipe_ingredient ri ON ro.recipe_id = ri.recipe_id
        JOIN inventory i ON ri.ingredient_id = i.id
        WHERE o.time BETWEEN %s AND %s
        GROUP BY i.ingredient, i.price
        ORDER BY used_quantity DESC
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, [start_dt, end_dt])
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        if not rows:
            return JsonResponse([], safe=False)

        # Format results as JSON
        result = [
            {
                'name': row[0],  # ingredient
                'used_quantity': int(row[1]),  # count (ensure it's int)
                'price': float(row[2])  # price
            }
            for row in rows
        ]
        return JsonResponse(result, safe=False)

    except Exception as e:
        print(f"Error executing product usage query: {str(e)}")
        return JsonResponse({"error": f"Database error: {str(e)}"}, status=500)

# ------------------- SALES REPORT -------------------
@require_GET
def sales_report(request):
    """
    Generate a sales report showing recipe performance within a date range.
    
    Executes raw SQL to aggregate recipe sales data from orders, joining with
    recipe_orders and recipes tables to calculate quantity sold for each menu item.
    
    Args:
        request (HttpRequest): GET request with query parameters:
            - start_date (str): Start datetime in ISO format (YYYY-MM-DDTHH:MM)
            - end_date (str): End datetime in ISO format (YYYY-MM-DDTHH:MM)
    
    Returns:
        JsonResponse: Array of recipe sales data or error
            Success (200): List of dictionaries containing:
                - id (int): Recipe ID
                - name (str): Recipe name
                - price (float): Recipe price
                - type (str): Recipe type/category
                - quantity_sold (int): Number of times ordered
                Ordered by quantity_sold descending (best sellers first)
            Error (400): Missing or invalid parameters
                - error (str): Description of parameter issue
            Error (500): Database error
                - error (str): Database error description
    
    Validation:
        - Both start_date and end_date are required
        - Dates must be valid ISO format (YYYY-MM-DDTHH:MM)
        - start_date must be before or equal to end_date
        
    Debug Output:
        Prints total recipe count and individual recipe details to console
        for debugging purposes.
        
    Note:
        Returns empty array if no orders found in date range.
        Includes all recipes ordered at least once, even if currently inactive.
    """
    start_str = request.GET.get("start_date")
    end_str = request.GET.get("end_date")

    if not start_str or not end_str:
        return JsonResponse({"error": "Missing start_date or end_date"}, status=400)

    try:
        start_dt = datetime.fromisoformat(start_str)
        end_dt = datetime.fromisoformat(end_str)
    except (ValueError, TypeError):
        return JsonResponse({"error": "Invalid date format. Use YYYY-MM-DDTHH:MM"}, status=400)

    if start_dt > end_dt:
        return JsonResponse({"error": "Start date must be before end date"}, status=400)

    # Use raw SQL query (like Java version) to join tables and aggregate
    query = """
        SELECT r.id, r.name, r.price, r.type, COUNT(ro.order_id) as quantity_sold
        FROM orders o
        JOIN recipe_orders ro ON o.id = ro.order_id
        JOIN recipes r ON ro.recipe_id = r.id
        WHERE o.time BETWEEN %s AND %s
        GROUP BY r.id, r.name, r.price, r.type
        ORDER BY quantity_sold DESC
    """

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, [start_dt, end_dt])
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        if not rows:
            return JsonResponse([], safe=False)

        print(f"DEBUG: Returning {len(rows)} recipes")
        
        # Format results as JSON
        result = [
            {
                'id': int(row[0]),  # recipe id
                'name': row[1],  # recipe name
                'price': float(row[2]),  # price
                'type': row[3],  # type
                'quantity_sold': int(row[4])  # quantity sold
            }
            for row in rows
        ]

        # Print every item
        for idx, item in enumerate(result):
            print(f"DEBUG [{idx}]: {item['name']} (ID: {item['id']}) - Sold: {item['quantity_sold']}, Price: ${item['price']}, Type: {item['type']}")

        return JsonResponse(result, safe=False)

    except Exception as e:
        print(f"Error executing sales report query: {str(e)}")
        return JsonResponse({"error": f"Database error: {str(e)}"}, status=500)

@require_GET
def x_report(request):
    """
    Generate an X Report showing hourly sales since the last Z Report.
    
    Creates a line graph visualization of sales by hour since the most recent
    Z Report timestamp. X Reports are interim reports that don't reset the
    sales period (unlike Z Reports which mark period boundaries).
    
    Args:
        request (HttpRequest): GET request (no parameters required)
    
    Returns:
        JsonResponse: Report data or error
            Success (200):
                - graph (str): Base64-encoded PNG image of hourly sales chart
                - total_sum (float): Total sales amount since last Z Report
            Error (500):
                - error (str): Exception message
    
    Report Details:
        - X-axis: Hours 0-23 with labels "HH:00"
        - Y-axis: Total price (sales amount)
        - Data points marked with circles
        - Non-zero values labeled above points
        - Title: "X Report: Orders Since Last Z Report"
        
    Side Effects:
        None - does not modify database or create new Z Report entry
        
    Note:
        If no Z Report exists, uses datetime.min as the baseline (all orders).
        Uses matplotlib with 'Agg' backend for server-side rendering.
        Graph dimensions: 14x4 inches.
    """
    try:
        # Get the most recent Z report timestamp
        last_z = orders_items_model.OrderZHistory.objects.order_by('-zreports').first()
        last_z_time = last_z.zreports if last_z else timezone.make_aware(datetime.min)

        # Get all orders since last Z report
        orders = orders_items_model.Order.objects.filter(time__gte=last_z_time)

        # Prepare hourly sums (0-23)
        hourly_totals = [0] * 24
        total_sum = 0  # <-- initialize total sum
        for order in orders:
            hour = order.time.hour
            hourly_totals[hour] += order.price
            total_sum += order.price  # <-- accumulate total sum

        # X-axis labels
        x_hours = list(range(24))
        y_prices = hourly_totals

        # Plot
        fig, ax = plt.subplots(figsize=(14, 4))
        ax.plot(x_hours, y_prices, marker='o', linestyle='-')

        # Add labels above each point if value > 0
        for x, y in zip(x_hours, y_prices):
            if y > 0:
                ax.text(x, y + max(y_prices)*0.02, f"{y:.2f}", ha='center', va='bottom', fontsize=9)

        # X-axis settings: one tick per hour
        ax.set_xlim(0, 23)
        ax.set_xticks(x_hours)
        ax.set_xticklabels([f"{h}:00" for h in x_hours], rotation=45, ha='right')

        # Titles and labels
        ax.set_title('X Report: Orders Since Last Z Report')
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Total Price')

        plt.tight_layout()

        # Save plot to PNG in memory
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)

        return JsonResponse({
            'graph': image_base64,
            'total_sum': round(total_sum, 2)  # <-- return total sum
        })

    except Exception as e:
        print("Error in x_report:", e)
        return JsonResponse({'error': str(e)}, status=500)

@require_GET
def z_report(request):
    """
    Generate a Z Report showing hourly sales since last Z Report, then reset.
    
    Creates a line graph visualization of sales by hour and creates a new
    Z Report entry marking the current time as the end of this sales period
    and start of the next. Z Reports represent end-of-day or period closings.
    
    Args:
        request (HttpRequest): GET request (no parameters required)
    
    Returns:
        JsonResponse: Report data or error
            Success (200):
                - graph (str): Base64-encoded PNG image of hourly sales chart
                - total_sum (float): Total sales amount for the period
            Error (500):
                - error (str): Exception message
    
    Report Details:
        - X-axis: Hours 0-23 with labels "HH:00"
        - Y-axis: Total price (sales amount)
        - Data points marked with circles
        - Non-zero values labeled above points
        - Title: "Z Report: [start_time] - [end_time]"
        
    Side Effects:
        - Creates new OrderZHistory record with current timestamp
        - This marks the boundary between sales periods
        
    Important:
        Running this report "closes" the current period. Subsequent X/Z reports
        will only include orders after this timestamp.
        
    Note:
        If no previous Z Report exists, uses datetime.min as baseline.
        Uses matplotlib with 'Agg' backend for server-side rendering.
        Graph dimensions: 14x4 inches.
        Times are displayed in local timezone.
    """
    try:
        # Get all orders since the last Z report
        last_z = orders_items_model.OrderZHistory.objects.order_by('-zreports').first()
        last_z_time = last_z.zreports if last_z else timezone.make_aware(datetime.min)

        orders = orders_items_model.Order.objects.filter(time__gte=last_z_time)

        # Prepare hourly sums (0-23)
        hourly_totals = [0] * 24
        total_sum = 0
        for order in orders:
            hour = order.time.hour
            hourly_totals[hour] += order.price
            total_sum += order.price

        # X-axis labels
        x_hours = list(range(24))
        y_prices = hourly_totals

        # Plot
        fig, ax = plt.subplots(figsize=(14, 4))
        ax.plot(x_hours, y_prices, marker='o', linestyle='-')

        # Add labels above each point if value > 0
        for x, y in zip(x_hours, y_prices):
            if y > 0:
                ax.text(x, y + max(y_prices)*0.02, f"{y:.2f}", ha='center', va='bottom', fontsize=9)

        # X-axis settings: one tick per hour
        ax.set_xlim(0, 23)
        ax.set_xticks(x_hours)
        ax.set_xticklabels([f"{h}:00" for h in x_hours], rotation=45, ha='right')

        # Titles and labels
        now = timezone.localtime()
        title_str = f"Z Report: {last_z_time.strftime('%Y-%m-%d %H:%M')} - {now.strftime('%Y-%m-%d %H:%M')}"
        ax.set_title(title_str)
        ax.set_xlabel('Hour of Day')
        ax.set_ylabel('Total Price')

        plt.tight_layout()

        # Save plot to PNG in memory
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        image_base64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)

        # # Create new Z report entry with current time
        orders_items_model.OrderZHistory.objects.create(zreports=now)

        return JsonResponse({
            'graph': image_base64,
            'total_sum': round(total_sum, 2)
        })

    except Exception as e:
        print("Error in z_report:", e)
        return JsonResponse({'error': str(e)}, status=500)

# INVENTORY MANAGEMENT FUNCTIONS #

# ------------------- INVENTORY PAGE (LIST ITEMS) -------------------
def inventory_page(request):
    """
    Render the inventory management page.
    
    Displays all inventory items in a list view for management purposes.
    Simple page render with no additional processing.
    
    Args:
        request (HttpRequest): Django request object
    
    Returns:
        HttpResponse: Rendered HTML template with context:
            - ingredients (QuerySet): All Inventory objects
            
    Template:
        manager/inventory.html
        
    Note:
        This appears to be a dedicated full-page view, separate from
        the tab_view('inventory') which serves the same template as a partial.
        Consider consolidating these two views to avoid duplication.
    """
    ingredients = recipes_model.Inventory.objects.all()
    return render(request, "manager/inventory.html", {
        "ingredients": ingredients
    })


@csrf_exempt
def add_inventory_item(request):
    """
    Create a new inventory item with validation.
    
    Validates all inventory fields including numeric types and non-negative
    values. Checks for duplicate ingredient names (case-insensitive).
    
    Args:
        request (HttpRequest): POST request containing:
            - ingredient (str): Ingredient/item name
            - quantity (str): Initial quantity (converted to int)
            - price (str): Price per unit (converted to float)
            - minimum_stock (str): Minimum stock threshold (converted to int)
    
    Returns:
        JsonResponse: Success or error response
            Success (200):
                - success (bool): True
                - message (str): Confirmation message
                - item (dict): Created inventory item with id, ingredient,
                  quantity, price (as float), and minimum_stock
            Error (200):
                - success (bool): False
                - errors (list[str]): Validation error messages
    
    Validation:
        - Name is required and must be unique (case-insensitive)
        - Quantity must be a non-negative integer
        - Price must be a non-negative number
        - Minimum stock must be a non-negative integer
        
    Side Effects:
        - Creates Inventory object
        
    Note:
        All numeric fields default to "0" string if not provided, then
        converted and validated. Consider making quantity/price required
        with no defaults for better data integrity.
    """
    if request.method == "POST":
        name = request.POST.get("ingredient", "").strip()
        quantity = request.POST.get("quantity", "0").strip()
        price = request.POST.get("price", "0").strip()
        minimum_stock = request.POST.get("minimum_stock", "0").strip()

        errors = []

        # Validation
        if not name:
            errors.append("Name is required.")

        try:
            quantity = int(quantity)
            if quantity < 0:
                errors.append("Quantity cannot be negative.")
        except ValueError:
            errors.append("Quantity must be a number.")

        try:
            price = float(price)
            if price < 0:
                errors.append("Price cannot be negative.")
        except ValueError:
            errors.append("Price must be a number.")

        try:
            minimum_stock = int(minimum_stock)
            if minimum_stock < 0:
                errors.append("Minimum stock cannot be negative.")
        except ValueError:
            errors.append("Minimum stock must be a number.")

        # Check for duplicates
        if recipes_model.Inventory.objects.filter(ingredient__iexact=name).exists():
            errors.append("Item already exists in inventory.")

        if errors:
            return JsonResponse({"success": False, "errors": errors})

        # Create new inventory item
        new_item = recipes_model.Inventory.objects.create(
            ingredient=name,
            quantity=quantity,
            price=price,
            minimum_stock=minimum_stock
        )

        return JsonResponse({
            "success": True,
            "message": f"{name} added successfully to inventory!",
            "item": {
                "id": new_item.id,
                "ingredient": new_item.ingredient,
                "quantity": new_item.quantity,
                "price": float(new_item.price),
                "minimum_stock": new_item.minimum_stock
            }
        })

    return JsonResponse({"success": False, "error": "Invalid request method."})


@csrf_exempt
def edit_inventory_item(request):
    """
    Update an existing inventory item's details.
    
    Modifies inventory item fields with validation. Does not check for
    duplicate names since inventory items should remain unique.
    
    Args:
        request (HttpRequest): POST request containing:
            - item_id (str): ID of inventory item to update
            - ingredient (str): Updated ingredient/item name
            - quantity (str): Updated quantity (converted to int)
            - price (str): Updated price (converted to float)
            - minimum_stock (str): Updated minimum stock (converted to int)
    
    Returns:
        JsonResponse: Success or error response
            Success (200):
                - success (bool): True
                - message (str): "Item updated successfully."
                - item (dict): Updated inventory item with id, ingredient,
                  quantity, price (as float), and minimum_stock
            Error (200):
                - success (bool): False
                - errors (list[str]): Validation error messages
                - error (str): "No item selected" or "Item not found"
    
    Validation:
        - item_id is required
        - Ingredient name is required
        - Quantity must be a valid integer
        - Price must be a valid number
        - Minimum stock must be a valid integer
        
    Side Effects:
        - Updates Inventory object fields
        
    Note:
        Does not validate for negative values (unlike add_inventory_item).
        Consider adding consistent validation across add/edit functions.
        Does not check for duplicate names with other items.
    """
    if request.method == "POST":
        item_id = request.POST.get("item_id")

        if not item_id:
            return JsonResponse({"success": False, "error": "No item selected."})

        try:
            ingredient = get_object_or_404(recipes_model.Inventory, id=item_id)
        except:
            return JsonResponse({"success": False, "error": "Item not found."})

        ingredient_name = request.POST.get("ingredient", "").strip()
        quantity = request.POST.get("quantity", "").strip()
        price = request.POST.get("price", "").strip()
        minimum_stock = request.POST.get("minimum_stock", "").strip()

        errors = []

        if not ingredient_name:
            errors.append("Ingredient name is required.")

        try:
            quantity_val = int(quantity)
        except ValueError:
            errors.append("Quantity must be a valid integer.")

        try:
            price_val = float(price)
        except ValueError:
            errors.append("Price must be a valid number.")

        try:
            minimum_stock_val = int(minimum_stock)
        except ValueError:
            errors.append("Minimum stock must be a valid integer.")

        if errors:
            return JsonResponse({"success": False, "errors": errors})

        # Update ingredient
        ingredient.ingredient = ingredient_name
        ingredient.quantity = quantity_val
        ingredient.price = price_val
        ingredient.minimum_stock = minimum_stock_val
        ingredient.save()

        return JsonResponse({
            "success": True,
            "message": "Item updated successfully.",
            "item": {
                "id": ingredient.id,
                "ingredient": ingredient.ingredient,
                "quantity": ingredient.quantity,
                "price": float(ingredient.price),
                "minimum_stock": ingredient.minimum_stock
            }
        })

    return JsonResponse({"success": False, "error": "Invalid request method."})


@csrf_exempt
def add_inventory_quantity(request):
    """
    Add quantity to an existing inventory item (restock operation).
    
    Increments the current quantity of an inventory item by the specified amount.
    Useful for restocking operations without needing to calculate the new total
    quantity manually.
    
    Args:
        request (HttpRequest): POST request containing:
            - item_id (str): ID of inventory item to restock
            - quantity_to_add (str): Amount to add (converted to float)
    
    Returns:
        JsonResponse: Success or error response
            Success (200):
                - success (bool): True
                - message (str): Confirmation with amount added
                - new_quantity (float): Updated total quantity
            Error (200):
                - success (bool): False
                - error (str): Error message ("Missing item or quantity",
                  "Invalid quantity", or "Item not found")
    
    Validation:
        - Both item_id and quantity_to_add are required
        - quantity_to_add must be a valid number
        - No restriction on negative values (could be used for adjustments)
        
    Side Effects:
        - Updates Inventory.quantity field
        - Handles None quantity gracefully by defaulting to 0
        
    Note:
        Uses float for quantity_to_add to support decimal amounts.
        Consider whether negative quantities should be allowed (could enable
        theft/loss recording) or blocked (use separate deduction function).
    """
    if request.method == "POST":
        item_id = request.POST.get("item_id")
        qty_to_add = request.POST.get("quantity_to_add")

        if not item_id or not qty_to_add:
            return JsonResponse({"success": False, "error": "Missing item or quantity."})

        try:
            qty_to_add = float(qty_to_add)
        except ValueError:
            return JsonResponse({"success": False, "error": "Invalid quantity."})

        try:
            ingredient = get_object_or_404(recipes_model.Inventory, id=item_id)
        except:
            return JsonResponse({"success": False, "error": "Item not found."})

        # Safeguard: default current quantity to 0 if None
        current_qty = ingredient.quantity if ingredient.quantity is not None else 0

        ingredient.quantity = current_qty + qty_to_add
        ingredient.save()

        return JsonResponse({
            "success": True,
            "message": f"Added {qty_to_add} to inventory.",
            "new_quantity": ingredient.quantity
        })

    return JsonResponse({"success": False, "error": "Invalid request method."})


@csrf_exempt
def delete_inventory_item(request):
    """
    Delete an inventory item from the database.
    
    Permanently removes the inventory item. Does not check if the item is
    currently used in any recipes, which could cause foreign key constraint
    violations or orphaned relationships.
    
    Args:
        request (HttpRequest): POST request containing:
            - item_id (str): ID of inventory item to delete
    
    Returns:
        JsonResponse: Success or error response
            Success (200):
                - success (bool): True
                - message (str): "Item deleted successfully."
            Error (200):
                - success (bool): False
                - error (str): Error message ("No item selected",
                  exception message, or "Invalid request method")
    
    Side Effects:
        - Deletes Inventory record
        - May cause issues if item is referenced in RecipeIngredient table
        
    Warning:
        No validation for:
        - Items currently used in recipes (RecipeIngredient relationships)
        - Items with pending orders
        Consider implementing:
        - Soft delete (is_available flag) instead of hard delete
        - Check for recipe dependencies before allowing deletion
        - Cascade delete or prevent delete of items in use
        - Admin-only permission check
    """
    if request.method == "POST":
        item_id = request.POST.get("item_id")

        if not item_id:
            return JsonResponse({"success": False, "error": "No item selected."})

        try:
            ingredient = get_object_or_404(recipes_model.Inventory, id=item_id)
            ingredient.delete()
            return JsonResponse({"success": True, "message": "Item deleted successfully."})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request method."})