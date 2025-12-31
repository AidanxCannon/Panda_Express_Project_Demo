// Global order state
let currentOrder = []; // Array of menu items (each containing an array of recipes)
let activeSelectionId = null; // tracks which order card is being edited
let orderIdCounter = 0;
let completedOrderCounter = 1001;
let cashierPriceMaps = {
    drinkPrices: {},
    drinkHasSizes: {},
    drinkSingle: {},
    appetizerPrices: {},
    alacartePrices: {},
    alacarteSizePrices: {},
    alacartePremiumPrices: {},
    alacartePremiumItems: new Set(),
};
let purchaseModal;
let purchaseModalNumberEl;
let purchaseModalTotalEl;
let purchaseModalOk;
let clearConfirmModal;
let confirmClearBtn;
let cancelClearBtn;
let warningBanner;
let warningTimer = null;

// Current category state
let currentCategory = 'bowl';
let currentSelection = {
    sides: [],
    entrees: [],
    recipes: []
};
// Snapshot of the item before editing; used to restore if user clears everything and leaves
let activeSelectionSnapshot = null;

// Category configuration
const categoryConfig = {
    'bowl': { maxSides: 1, maxEntrees: 1, menuItemName: 'Bowl' },
    'plate': { maxSides: 1, maxEntrees: 2, menuItemName: 'Plate' },
    'bigger-plate': { maxSides: 2, maxEntrees: 3, menuItemName: 'Bigger Plate' },
    'a-la-carte': { maxSides: 1, maxEntrees: 1, menuItemName: 'A La Carte' },
    'appetizers': { maxAppetizers: 1, menuItemName: 'Appetizer' },
    'drinks': { maxDrinks: 1, menuItemName: 'Drink' }
};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    // Load pricing maps from JSON script tags
    const parseJsonScript = (id) => {
        const el = document.getElementById(id);
        if (!el) return {};
        try { return JSON.parse(el.textContent); } catch (e) { return {}; }
    };
    cashierPriceMaps.drinkPrices = parseJsonScript('cashier-drink-prices');
    cashierPriceMaps.drinkHasSizes = parseJsonScript('cashier-drink-has-sizes');
    cashierPriceMaps.drinkSingle = parseJsonScript('cashier-drink-single-prices');
    cashierPriceMaps.appetizerPrices = parseJsonScript('cashier-appetizer-prices');
    cashierPriceMaps.alacartePrices = parseJsonScript('cashier-alacarte-prices');
    cashierPriceMaps.alacarteSizePrices = parseJsonScript('cashier-alacarte-size-prices');
    cashierPriceMaps.alacartePremiumPrices = parseJsonScript('cashier-alacarte-premium-prices');
    cashierPriceMaps.alacartePremiumItems = new Set(parseJsonScript('cashier-alacarte-premium-items') || []);

    purchaseModal = document.getElementById('purchaseModal');
    purchaseModalNumberEl = document.getElementById('purchaseModalNumber');
    purchaseModalTotalEl = document.getElementById('purchaseModalTotal');
    purchaseModalOk = document.getElementById('purchaseModalOk');
    clearConfirmModal = document.getElementById('clearConfirmModal');
    confirmClearBtn = document.getElementById('confirmClearOrder');
    cancelClearBtn = document.getElementById('cancelClearOrder');
    warningBanner = document.getElementById('cashier-warning');
    if (purchaseModal) {
        purchaseModal.addEventListener('click', (event) => {
            if (event.target === purchaseModal) {
                hidePurchaseModal();
                resetCashierInterface();
            }
        });
    }
    if (purchaseModalOk) {
        purchaseModalOk.addEventListener('click', () => {
            hidePurchaseModal();
            resetCashierInterface();
        });
    }
    setupClearOrderModal();
    setupCategoryNavigation();
    setupBowlSelection();
    setupPlateSelection();
    setupBiggerPlateSelection();
    setupALaCarteSelection();
    setupAppetizersSelection();
    setupDrinksSelection();
    setupAddToOrderButtons();
    setupOrderItemClickDelegation();
    setupOrderItemClickDelegation();
    [
        'bowl-sides',
        'bowl-entrees',
        'bowl-entrees',
        'plate-entrees',
        'bigger-plate-entrees',
        'alacarte-entrees',
        'appetizers-grid',
        'drinks-grid'
    ].forEach(setupPagination);
});

// Category navigation
function setupCategoryNavigation() {
    document.querySelectorAll('.nav-button').forEach(btn => {
        btn.addEventListener('click', () => {
            // If we were editing and currentSelection is empty, restore snapshot before switching
            if (activeSelectionId !== null && isSelectionEmpty(currentSelection) && activeSelectionSnapshot) {
                restoreActiveSelectionFromSnapshot();
            }
            // If switching to a different view while an order card is active, clear selections
            if (activeSelectionId !== null && btn.dataset.category !== currentCategory) {
                activeSelectionId = null;
                resetSelection();
                highlightActiveOrderItem();
            }

            document.querySelectorAll('.category-view').forEach(view => {
                view.classList.remove('active');
            });

            const viewId = `${btn.dataset.category}-view`;
            const viewElement = document.getElementById(viewId);
            if (viewElement) {
                viewElement.classList.add('active');
            }

            document.querySelectorAll('.nav-button').forEach(b => {
                b.classList.remove('active-category');
            });
            btn.classList.add('active-category');

            currentCategory = btn.dataset.category;
            resetSelection();
        });
    });

    const initialButton = document.querySelector('.nav-button[data-category="bowl"]');
    if (initialButton) {
        initialButton.click();
    }
}

// Pagination helper for grids (4 per row, 8 per page)
function setupPagination(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    const controls = document.querySelector(`.selection-controls[data-pagination="${containerId}"]`);
    const items = Array.from(container.children || []);
    const perPage = 8; // 2 rows of 4
    let page = 0;
    const totalPages = Math.max(1, Math.ceil(items.length / perPage));

    function renderPage() {
        items.forEach((btn, idx) => {
            const start = page * perPage;
            const end = start + perPage;
            btn.style.display = (idx >= start && idx < end) ? '' : 'none';
        });
        if (controls) {
            controls.innerHTML = '';
            if (totalPages > 1) {
                const prev = document.createElement('button');
                prev.textContent = 'Prev';
                prev.disabled = page === 0;
                prev.addEventListener('click', () => {
                    page = Math.max(0, page - 1);
                    renderPage();
                });
                const next = document.createElement('button');
                next.textContent = 'Next';
                next.disabled = page >= totalPages - 1;
                next.addEventListener('click', () => {
                    page = Math.min(totalPages - 1, page + 1);
                    renderPage();
                });
                controls.appendChild(prev);
                const indicator = document.createElement('span');
                indicator.textContent = ` ${page + 1}/${totalPages} `;
                indicator.style.color = '#fff';
                indicator.style.fontSize = '0.8rem';
                controls.appendChild(indicator);
                controls.appendChild(next);
            }
        }
    }
    renderPage();
}
function resetSelection() {
    currentSelection = {
        sides: [],
        entrees: [],
        recipes: []
    };
    clearSelectionButtons();
}

function clearSelectionButtons() {
    document.querySelectorAll('.selection-btn').forEach(btn => {
        btn.classList.remove('selected');
        btn.classList.remove('active');
        const badge = btn.querySelector('.selection-badge');
        if (badge && !badge.classList.contains('meal-qty-card__count')) badge.remove();
    });
    clearQtyCards();
}

function clearQtyCards() {
    document.querySelectorAll('.meal-qty-card').forEach(card => {
        card.dataset.qty = '0';
        const badge = card.querySelector('.meal-qty-card__count');
        if (badge) {
            badge.textContent = '0';
            badge.hidden = true;
            badge.style.display = 'none';
        }
        card.classList.remove('selected');
    });
    document.querySelectorAll('.side-count').forEach(el => { el.textContent = '0/2'; });
    document.querySelectorAll('.entree-count').forEach(el => {
        const max = el.dataset.max || el.textContent.split('/')[1] || '';
        el.textContent = max ? `0/${max}` : '0';
    });
}

// Bowl selection (1 side, 1 entree)
function setupBowlSelection() {
    const sidesContainer = document.getElementById('bowl-sides');
    const entreesContainer = document.getElementById('bowl-entrees');

    setupSideQtyCards(sidesContainer, 2, 1); // allow up to 2 halves total, max 1 per card
    setupEntreeQtyCards(entreesContainer, 1);
}

function updateCountIndicator(sourceId, total, max) {
    const el = document.querySelector(`[data-count-source="${sourceId}"]`);
    if (el) {
        el.textContent = `${total}/${max}`;
        el.dataset.max = max;
    }
}

// Plate selection (1 side, 2 entrees)
function setupPlateSelection() {
    const sidesContainer = document.getElementById('plate-sides');
    const entreesContainer = document.getElementById('plate-entrees');

    setupSideQtyCards(sidesContainer, 2, 1);
    setupEntreeQtyCards(entreesContainer, 2);
}

// Bigger Plate selection (1 side, 3 entrees)
function setupBiggerPlateSelection() {
    const sidesContainer = document.getElementById('bigger-plate-sides');
    const entreesContainer = document.getElementById('bigger-plate-entrees');

    setupSideQtyCards(sidesContainer, 2, 1);
    setupEntreeQtyCards(entreesContainer, 3);
}

// A La Carte selection (1 side or 1 entree)
function setupALaCarteSelection() {
    document.querySelectorAll('#a-la-carte-view .alacarte-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // Clear all previous selections in a la carte
            document.querySelectorAll('#a-la-carte-view .alacarte-btn').forEach(b => {
                b.classList.remove('selected');
            });
            
            currentSelection.recipes = [];
            this.classList.add('selected');
            
            const recipe = {
                id: this.dataset.recipeId,
                name: this.dataset.recipeName,
                type: this.dataset.recipeType,
                size: (document.querySelector('input[name=\"alacarte-size\"]:checked') || {}).value || 'M',
                price: 0
            };
            const isPremium = cashierPriceMaps.alacartePremiumItems.has(recipe.name);
            const map = cashierPriceMaps.alacartePrices[recipe.name] || (isPremium ? cashierPriceMaps.alacartePremiumPrices : cashierPriceMaps.alacarteSizePrices);
            recipe.price = (map && map[recipe.size]) || 0;
            currentSelection.recipes.push(recipe);
            updateActiveOrderItemFromSelection();
        });
    });
    document.querySelectorAll('input[name="alacarte-size"]').forEach(input => {
        input.addEventListener('change', () => {
            if (!currentSelection.recipes.length) return;
            const recipe = currentSelection.recipes[0];
            recipe.size = (document.querySelector('input[name="alacarte-size"]:checked') || {}).value || 'M';
            const isPremium = cashierPriceMaps.alacartePremiumItems.has(recipe.name);
            const map = cashierPriceMaps.alacartePrices[recipe.name] || (isPremium ? cashierPriceMaps.alacartePremiumPrices : cashierPriceMaps.alacarteSizePrices);
            recipe.price = (map && map[recipe.size]) || 0;
            updateActiveOrderItemFromSelection();
        });
    });
}

// Appetizers selection
function setupAppetizersSelection() {
    document.querySelectorAll('.appetizer-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.appetizer-btn').forEach(b => b.classList.remove('selected'));
            currentSelection.recipes = [];
            this.classList.add('selected');
            const recipe = {
                id: this.dataset.recipeId,
                name: this.dataset.recipeName,
                type: this.dataset.recipeType,
                size: (document.querySelector('input[name="appetizer-size"]:checked') || {}).value || 'M',
                price: 0,
            };
            const map = cashierPriceMaps.appetizerPrices[recipe.name] || {};
            recipe.price = map[recipe.size] || 0;
            currentSelection.recipes.push(recipe);
            updateActiveOrderItemFromSelection();
        });
    });

    document.querySelectorAll('input[name="appetizer-size"]').forEach(input => {
        input.addEventListener('change', () => {
            if (!currentSelection.recipes.length) return;
            const recipe = currentSelection.recipes[0];
            recipe.size = (document.querySelector('input[name="appetizer-size"]:checked') || {}).value || 'M';
            const map = cashierPriceMaps.appetizerPrices[recipe.name] || {};
            recipe.price = map[recipe.size] || 0;
            updateActiveOrderItemFromSelection();
        });
    });
}

// Drinks selection
function setupDrinksSelection() {
    const drinkButtons = document.querySelectorAll('.drink-btn');
    const sizeToggle = document.querySelector('#drinks-view .kiosk-size-toggle');
    const sizeInputs = document.querySelectorAll('input[name="drink-size"]');

    const getDrinkPrice = (name, size) => {
        const map = cashierPriceMaps.drinkPrices[name] || {};
        const hasSizes = cashierPriceMaps.drinkHasSizes[name];
        return hasSizes
            ? (map[size] || map['M'] || 0)
            : (cashierPriceMaps.drinkSingle[name] || map['M'] || 0);
    };

    const applySizeState = (name) => {
        const hasSizes = cashierPriceMaps.drinkHasSizes[name];
        if (!hasSizes) {
            sizeInputs.forEach(input => {
                input.disabled = true;
                input.checked = input.value === 'M';
            });
            if (sizeToggle) sizeToggle.classList.add('kiosk-size-toggle--disabled');
        } else {
            sizeInputs.forEach(input => input.disabled = false);
            if (sizeToggle) sizeToggle.classList.remove('kiosk-size-toggle--disabled');
        }
    };
    drinkButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            drinkButtons.forEach(b => b.classList.remove('selected'));
            currentSelection.recipes = [];
            this.classList.add('selected');
            applySizeState(this.dataset.recipeName);
            const recipe = {
                id: this.dataset.recipeId,
                name: this.dataset.recipeName,
                type: this.dataset.recipeType,
                size: (document.querySelector('input[name="drink-size"]:checked') || {}).value || 'M',
                price: 0,
            };
            recipe.price = getDrinkPrice(recipe.name, recipe.size);
            currentSelection.recipes.push(recipe);
            updateActiveOrderItemFromSelection();
        });
    });

    sizeInputs.forEach(input => {
        input.addEventListener('change', () => {
            const selected = document.querySelector('.drink-btn.selected');
            if (!selected || !currentSelection.recipes.length) return;
            const recipe = currentSelection.recipes[0];
            recipe.size = (document.querySelector('input[name="drink-size"]:checked') || {}).value || 'M';
            recipe.price = getDrinkPrice(recipe.name, recipe.size);
            updateActiveOrderItemFromSelection();
        });
    });
}

// Handle single selection (like 1 side)
function handleSingleSelection(container, button, type) {
    // Clear all selections in this container
    container.querySelectorAll('button').forEach(btn => {
        btn.classList.remove('selected');
    });
    
    // Clear the type array
    currentSelection[type] = [];
    
    // Add new selection
    button.classList.add('selected');
    const recipe = {
        id: button.dataset.recipeId,
        name: button.dataset.recipeName,
        type: button.dataset.recipeType,
        price: parseFloat(button.dataset.recipePrice) || 0
    };
    currentSelection[type].push(recipe);
    updateActiveOrderItemFromSelection();
}

// Handle split side selection (allows selecting 2 halves)
function handleSplitSideSelection(container, button, type, maxHalves) {
    const recipeId = button.dataset.recipeId;
    const currentCount = currentSelection[type].filter(r => r.id === recipeId).length;
    
    if (currentCount > 0) {
        // Already selected - add another half if under limit
        if (currentSelection[type].length < maxHalves) {
            const recipe = {
                id: button.dataset.recipeId,
                name: button.dataset.recipeName,
                type: button.dataset.recipeType,
                price: parseFloat(button.dataset.recipePrice) || 0,
                isHalf: true
            };
            currentSelection[type].push(recipe);
            updateSelectionBadge(button, currentCount + 1);
        } else {
            showCashierWarning(`You can only select up to ${maxHalves} half sides`);
        }
    } else {
        // Not selected yet - add first half
        if (currentSelection[type].length < maxHalves) {
            button.classList.add('selected');
            const recipe = {
                id: button.dataset.recipeId,
                name: button.dataset.recipeName,
                type: button.dataset.recipeType,
                price: parseFloat(button.dataset.recipePrice) || 0,
                isHalf: true
            };
            currentSelection[type].push(recipe);
            updateSelectionBadge(button, 1);
        } else {
            showCashierWarning(`You can only select up to ${maxHalves} half sides`);
        }
    }
    updateActiveOrderItemFromSelection();
}

// Handle split side selection (allows selecting 2 halves)
function handleSplitSideSelection(container, button, type, maxHalves) {
    const recipeId = button.dataset.recipeId;
    const currentCount = currentSelection[type].filter(r => r.id === recipeId).length;
    
    if (currentCount > 0) {
        // Already selected - add another half if under limit
        if (currentSelection[type].length < maxHalves) {
            const recipe = {
                id: button.dataset.recipeId,
                name: button.dataset.recipeName,
                type: button.dataset.recipeType,
                price: parseFloat(button.dataset.recipePrice) || 0,
                isHalf: true
            };
            currentSelection[type].push(recipe);
            updateSelectionBadge(button, currentCount + 1);
        } else {
            showCashierWarning(`You can only select up to ${maxHalves} half sides`);
        }
    } else {
        // Not selected yet - add first half
        if (currentSelection[type].length < maxHalves) {
            button.classList.add('selected');
            const recipe = {
                id: button.dataset.recipeId,
                name: button.dataset.recipeName,
                type: button.dataset.recipeType,
                price: parseFloat(button.dataset.recipePrice) || 0,
                isHalf: true
            };
            currentSelection[type].push(recipe);
            updateSelectionBadge(button, 1);
        } else {
            showCashierWarning(`You can only select up to ${maxHalves} half sides`);
        }
    }
    updateActiveOrderItemFromSelection();
}

// Update selection badge to show quantity
function updateSelectionBadge(button, count) {
    let badge = button.querySelector('.selection-badge');
    if (count > 1) {
        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'selection-badge';
            button.appendChild(badge);
        }
        badge.textContent = count;
    } else if (badge) {
        badge.remove();
    }
}

// Handle deselection (right-click to remove one instance)
function handleDeselection(container, button, type) {
    const recipeId = button.dataset.recipeId;
    const index = currentSelection[type].findIndex(r => r.id === recipeId);
    
    if (index !== -1) {
        // Remove one instance
        currentSelection[type].splice(index, 1);
        const newCount = currentSelection[type].filter(r => r.id === recipeId).length;
        
        if (newCount === 0) {
            button.classList.remove('selected');
        }
        updateSelectionBadge(button, newCount);
        updateActiveOrderItemFromSelection();
    }
}

// Handle multiple selection (like 2 or 3 entrees)
function handleMultipleSelection(container, button, type, max) {
    const recipeId = button.dataset.recipeId;
    const currentCount = currentSelection[type].filter(r => r.id === recipeId).length;
    
    if (currentCount > 0) {
        // Already selected - add another if under limit
        if (currentSelection[type].length < max) {
            const recipe = {
                id: button.dataset.recipeId,
                name: button.dataset.recipeName,
                type: button.dataset.recipeType,
                price: parseFloat(button.dataset.recipePrice) || 0
            };
            currentSelection[type].push(recipe);
            updateSelectionBadge(button, currentCount + 1);
        } else {
            showCashierWarning(`You can only select ${max} ${type}`);
        }
    } else {
        // Not selected yet - add first one
        if (currentSelection[type].length < max) {
            button.classList.add('selected');
            const recipe = {
                id: button.dataset.recipeId,
                name: button.dataset.recipeName,
                type: button.dataset.recipeType,
                price: parseFloat(button.dataset.recipePrice) || 0
            };
            currentSelection[type].push(recipe);
            updateSelectionBadge(button, 1);
        } else {
            showCashierWarning(`You can only select ${max} ${type}`);
        }
    }
    if (['a-la-carte', 'appetizers', 'drinks'].includes(item.category)) {
        const first = otherRecipes[0];
        if (first) {
            // preserve size on restore
            currentSelection.recipes = [{
                ...first,
                price: first.price || 0,
            }];
            if (item.category === 'a-la-carte') {
                const size = first.size || 'M';
                const input = document.querySelector(`input[name="alacarte-size"][value="${size}"]`);
                if (input) input.checked = true;
            } else if (item.category === 'appetizers') {
                    const size = first.size || 'M';
                    const input = document.querySelector(`input[name="appetizer-size"][value="${size}"]`);
                    if (input) input.checked = true;
                } else if (item.category === 'drinks') {
                    const size = first.size || 'M';
                    const input = document.querySelector(`input[name="drink-size"][value="${size}"]`);
                    if (input) input.checked = true;
                }
            }
        }

    updateActiveOrderItemFromSelection();
}

// Quantity-based entree cards (cashier view)
function setupEntreeQtyCards(container, maxEntrees) {
    if (!container) return;
    const cards = container.querySelectorAll('.meal-qty-card');

    const updateCardVisual = (card) => {
        const qty = Number(card.dataset.qty || 0);
        const badge = card.querySelector('.meal-qty-card__count');
        if (badge) {
            badge.textContent = qty;
            const show = qty > 0;
            badge.hidden = !show;
            badge.style.display = show ? 'flex' : 'none';
        }
        card.classList.toggle('selected', qty > 0);
    };

    const syncSelection = () => {
        currentSelection.entrees = [];
        cards.forEach(card => {
            const qty = Number(card.dataset.qty || 0);
            if (qty > 0) {
                const recipe = {
                    id: card.dataset.recipeId,
                    name: card.dataset.recipeName,
                    type: card.dataset.recipeType,
                    price: parseFloat(card.dataset.recipePrice) || 0
                };
                for (let i = 0; i < qty; i += 1) {
                    currentSelection.entrees.push(recipe);
                }
            }
        });
        updateActiveOrderItemFromSelection();
        updateCountIndicator(container.id, getTotal(), maxEntrees);
    };

        const getTotal = () => Array.from(cards).reduce((sum, c) => sum + (Number(c.dataset.qty || 0)), 0);

    const adjust = (card, delta) => {
        const current = Number(card.dataset.qty || 0);
        const total = getTotal();
        const others = total - current;
        const allowed = Math.max(0, maxEntrees - others);
        let next = current + delta;
        if (next < 0) next = 0;
        if (next > allowed) {
            showCashierWarning(`You can select up to ${maxEntrees} entree${maxEntrees > 1 ? 's' : ''}`);
            return;
        }
        card.dataset.qty = String(next);
        updateCardVisual(card);
        syncSelection();
        updateCountIndicator(container.id, getTotal(), maxTotal);
    };

    cards.forEach(card => {
        card.dataset.qty = card.dataset.qty || '0';
        updateCardVisual(card);
        card.querySelectorAll('.qty-bubble').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const delta = btn.dataset.action === 'increment' ? 1 : -1;
                adjust(card, delta);
            });
        });
    });
    // initial counts
    const total = getTotal();
    updateCountIndicator(container.id, total, maxEntrees);
}

// Side qty cards (max 1 per card, total up to 2 halves)
function setupSideQtyCards(container, maxTotal, maxPerCard) {
    if (!container) return;
    const cards = container.querySelectorAll('.meal-qty-card');

    const updateCardVisual = (card) => {
        const qty = Number(card.dataset.qty || 0);
        const badge = card.querySelector('.meal-qty-card__count');
        if (badge) {
            badge.textContent = qty;
            const show = qty > 0;
            badge.hidden = !show;
            badge.style.display = show ? 'flex' : 'none';
        }
        card.classList.toggle('selected', qty > 0);
    };

    const syncSelection = () => {
        currentSelection.sides = [];
        const totalSelections = Array.from(cards).reduce((sum, card) => sum + (Number(card.dataset.qty || 0)), 0);
        cards.forEach(card => {
            const qty = Number(card.dataset.qty || 0);
            if (qty > 0) {
                const recipe = {
                    id: card.dataset.recipeId,
                    name: card.dataset.recipeName,
                    type: card.dataset.recipeType,
                    price: parseFloat(card.dataset.recipePrice) || 0,
                    isHalf: (maxTotal === 2 && totalSelections === 2)
                };
                for (let i = 0; i < qty; i += 1) {
                    currentSelection.sides.push(recipe);
                }
            }
        });
        // If we cleared sides entirely while editing, restore from snapshot instead of wiping the item
        if (activeSelectionId !== null && isSelectionEmpty({ ...currentSelection, entrees: [], recipes: [] }) && activeSelectionSnapshot) {
            restoreActiveSelectionFromSnapshot();
        } else {
            updateActiveOrderItemFromSelection();
        }
        updateCountIndicator(container.id, totalSelections, maxTotal);
    };

    const getTotal = () => Array.from(cards).reduce((sum, c) => sum + (Number(c.dataset.qty || 0)), 0);

    const adjust = (card, delta) => {
        const current = Number(card.dataset.qty || 0);
        const total = getTotal();
        const others = total - current;
        const allowed = Math.max(0, maxTotal - others);
        let next = current + delta;
        if (next < 0) next = 0;
        if (next > maxPerCard) next = maxPerCard;
        if (next > allowed) {
            showCashierWarning(`You can select up to ${maxTotal} half sides (or 1 full side)`);
            return;
        }
        card.dataset.qty = String(next);
        updateCardVisual(card);
        syncSelection();
        updateCountIndicator(container.id, getTotal(), maxTotal);
    };

    cards.forEach(card => {
        card.dataset.qty = card.dataset.qty || '0';
        updateCardVisual(card);
        card.querySelectorAll('.qty-bubble').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const delta = btn.dataset.action === 'increment' ? 1 : -1;
                adjust(card, delta);
            });
        });
    });
    const total = getTotal();
    updateCountIndicator(container.id, total, maxTotal);
}

// Setup add to order buttons
function setupAddToOrderButtons() {
    document.getElementById('add-bowl-btn').addEventListener('click', function() {
        addMenuItem('bowl', 1, 1);
    });
    const clearBowl = document.getElementById('clear-bowl-btn');
    if (clearBowl) {
        clearBowl.addEventListener('click', () => {
            resetSelection();
            clearQtyCards();
            highlightActiveOrderItem();
        });
    }

    document.getElementById('add-plate-btn').addEventListener('click', function() {
        addMenuItem('plate', 1, 2);
    });
    const clearPlate = document.getElementById('clear-plate-btn');
    if (clearPlate) {
        clearPlate.addEventListener('click', () => {
            resetSelection();
            clearQtyCards();
            highlightActiveOrderItem();
        });
    }

    document.getElementById('add-bigger-plate-btn').addEventListener('click', function() {
        addMenuItem('bigger-plate', 2, 3);
    });
    const clearBigger = document.getElementById('clear-bigger-plate-btn');
    if (clearBigger) {
        clearBigger.addEventListener('click', () => {
            resetSelection();
            clearQtyCards();
            highlightActiveOrderItem();
        });
    }
    const clearAlacarte = document.getElementById('clear-alacarte-btn');
    if (clearAlacarte) {
        clearAlacarte.addEventListener('click', () => {
            resetSelection();
            clearQtyCards();
            highlightActiveOrderItem();
        });
    }
    const clearAppetizer = document.getElementById('clear-appetizer-btn');
    if (clearAppetizer) {
        clearAppetizer.addEventListener('click', () => {
            resetSelection();
            clearQtyCards();
            highlightActiveOrderItem();
        });
    }
    const clearDrinkBtn = document.getElementById('clear-drink-btn');
    if (clearDrinkBtn) {
        clearDrinkBtn.addEventListener('click', () => {
            resetSelection();
            clearQtyCards();
            highlightActiveOrderItem();
        });
    }

    document.getElementById('add-alacarte-btn').addEventListener('click', function() {
        addMenuItem('a-la-carte', 0, 0);
    });

    document.getElementById('add-appetizer-btn').addEventListener('click', function() {
        addMenuItem('appetizers', 0, 0);
    });

    document.getElementById('add-drink-btn').addEventListener('click', function() {
        addMenuItem('drinks', 0, 0);
    });
    const clearDrink = document.getElementById('clear-drink-btn');
    if (clearDrink) {
        clearDrink.addEventListener('click', () => {
            resetSelection();
            clearQtyCards();
            highlightActiveOrderItem();
        });
    }

    document.getElementById('add-protein-plate-btn').addEventListener('click', function() {
        addMenuItem('protein-plate', 0, 0);
    });
}

// Add menu item to order
function addMenuItem(category, requiredSides, requiredEntrees) {
    const config = categoryConfig[category];
    
    // Validation based on category
    if (category === 'bowl' || category === 'plate' || category === 'bigger-plate') {
        // For sides: bowls and plates allow 1-2 (for split sides), bigger plates allow up to 2
        const maxSides = (category === 'bowl' || category === 'plate') ? 2 : config.maxSides;
        if (currentSelection.sides.length < 1 || currentSelection.sides.length > maxSides) {
            if (category === 'bowl' || category === 'plate') {
                showCashierWarning(`Please select 1 side or 2 half sides`);
            } else {
                showCashierWarning(`Please select ${requiredSides} side(s)`);
            }
            return;
        }
        if (currentSelection.entrees.length < 1 || currentSelection.entrees.length > (config.maxEntrees || requiredEntrees)) {
            showCashierWarning(`Please select ${requiredEntrees} entree(s)`);
            return;
        }
    } else if (category === 'a-la-carte' || category === 'appetizers' || category === 'drinks') {
        if (currentSelection.recipes.length === 0) {
            showCashierWarning('Please select an item');
            return;
        }
    }

    // Combine all recipes
    const allRecipes = buildCurrentRecipes();

    // Calculate price based on category
    let price = 0.00;
    
    if (category === 'bowl') {
        // Bowl: $8.30 + premium prices
        price = 8.30;
        currentSelection.entrees.forEach(entree => {
            price += entree.price;
        });
    } else if (category === 'plate') {
        // Plate: $12.15 + premium prices
        price = 12.15;
        currentSelection.entrees.forEach(entree => {
            price += entree.price;
        });
    } else if (category === 'bigger-plate') {
        // Bigger Plate: $14.05 + premium prices
        price = 14.05;
        currentSelection.entrees.forEach(entree => {
            price += entree.price;
        });
    } else if (category === 'a-la-carte') {
        const size = (document.querySelector('input[name="alacarte-size"]:checked') || {}).value || 'M';
        currentSelection.recipes.forEach(recipe => {
            const isPremium = cashierPriceMaps.alacartePremiumItems.has(recipe.name);
            const priceMap = cashierPriceMaps.alacartePrices[recipe.name] || (isPremium ? cashierPriceMaps.alacartePremiumPrices : cashierPriceMaps.alacarteSizePrices);
            const p = (priceMap && priceMap[size]) || 0;
            recipe.size = size;
            price += p;
            recipe.price = p;
        });
    } else if (category === 'appetizers') {
        const size = (document.querySelector('input[name="appetizer-size"]:checked') || {}).value || 'M';
        currentSelection.recipes.forEach(recipe => {
            const map = cashierPriceMaps.appetizerPrices[recipe.name] || {};
            const p = map[size] || 0;
            recipe.size = size;
            recipe.price = p;
            price += p;
        });
    } else if (category === 'drinks') {
        currentSelection.recipes.forEach(recipe => {
            const map = cashierPriceMaps.drinkPrices[recipe.name] || {};
            const hasSizes = cashierPriceMaps.drinkHasSizes[recipe.name];
            const size = hasSizes ? ((document.querySelector('input[name="drink-size"]:checked') || {}).value || 'M') : 'M';
            const p = hasSizes ? (map[size] || map['M'] || 0) : (cashierPriceMaps.drinkSingle[recipe.name] || map['M'] || 0);
            recipe.size = size;
            recipe.price = p;
            price += p;
        });
    }

    // Create menu item
    const menuItem = {
        id: orderIdCounter++,
        menuItemName: config.menuItemName,
        category: category,
        recipes: allRecipes,
        price: price
    };

    // Add to order
    currentOrder.push(menuItem);
    updateOrderDisplay();
    
    // Reset selection only when not editing an existing item; keep selections if duplicating
    // Keep selections after adding to allow quick repeat/edits
    highlightActiveOrderItem();
}

// Update order display
function updateOrderDisplay() {
    const orderItemsDiv = document.getElementById('order-items');
    
    if (currentOrder.length === 0) {
        orderItemsDiv.innerHTML = '<p class="empty-message">No items in order</p>';
    } else {
        orderItemsDiv.innerHTML = currentOrder.map(item => {
            // Count duplicate recipes and display with quantities
            const recipeCounts = {};
            item.recipes.forEach(r => {
                const baseName = r.name;
                const sizeLabel = r.size ? ` (${r.size})` : '';
                const key = `${baseName}${sizeLabel}`;
                if (!recipeCounts[key]) {
                    recipeCounts[key] = { count: 0, isHalf: r.isHalf || false };
                }
                recipeCounts[key].count += 1;
            });
            const recipesList = Object.entries(recipeCounts)
                .map(([name, data]) => {
                    if (data.isHalf && data.count === 1) {
                        return `${name} (Half)`;
                    } else if (data.count > 1) {
                        return `${name} (×${data.count})`;
                    }
                    return name;
                })
                .join(', ');
            const activeClass = (item.id === activeSelectionId) ? 'order-item--active' : '';
            return `
                <article class="order-item ${activeClass}" data-order-id="${item.id}" onclick="viewOrderItem(${item.id})">
                    <div class="order-item-header">
                        <strong>${item.menuItemName}</strong>
                        <button class="ghost-button" data-remove-id="${item.id}" onclick="removeFromOrder(event, ${item.id})">Remove</button>
                    </div>
                    <p class="order-item-recipes">${recipesList}</p>
                    <p class="order-item-price">$${item.price.toFixed(2)}</p>
                </article>
            `;
        }).join('');
    }

    updateTotals();
    // Preserve current selections/visuals to allow quick repeats/edits
    highlightActiveOrderItem();
}

// Remove from order
function removeFromOrder(evt, orderId) {
    if (evt) {
        evt.stopPropagation();
    }
    currentOrder = currentOrder.filter(item => item.id !== orderId);
    if (activeSelectionId === orderId) {
        activeSelectionId = null;
        resetSelection();
    }
    updateOrderDisplay();
}

// Jump to an order item for editing
function viewOrderItem(orderId) {
    const item = currentOrder.find(o => o.id === orderId);
    if (!item) return;

    // Toggle off if already active: deselect card and clear editing state without altering saved item
    if (activeSelectionId === orderId) {
        activeSelectionId = null;
        activeSelectionSnapshot = null;
        resetSelection();
        // Clear any visible selections (counts, badges, borders)
        clearSelectionButtons();
        clearQtyCards();
        // Reset size radios for single-select categories
        ['alacarte-size', 'appetizer-size', 'drink-size'].forEach(name => {
            const inputs = Array.from(document.querySelectorAll(`input[name="${name}"]`));
            if (inputs.length === 0) return;
            inputs.forEach(input => { input.checked = false; });
            const fallback = inputs.find(i => i.defaultChecked) || inputs[0];
            fallback.checked = true;
        });
        highlightActiveOrderItem();
        updateOrderDisplay();
        return;
    }

    // Focus the clicked item and show its selections
    activeSelectionId = orderId;
    // Take a snapshot of the item before edits so we can restore if user clears everything
    activeSelectionSnapshot = {
        id: item.id,
        category: item.category,
        menuItemName: item.menuItemName,
        recipes: JSON.parse(JSON.stringify(item.recipes || [])),
        price: item.price
    };
    highlightActiveOrderItem();

    // Switch to the item's category/view
    const navBtn = document.querySelector(`.nav-button[data-category="${item.category}"]`);
    if (navBtn) {
        navBtn.click();
    }

    // Apply selections after view switches
    setTimeout(() => {
        applyItemSelections(item);
        highlightActiveOrderItem();
    }, 0);
}

// Delegate clicks on order items (navigate to view / show selections) and remove buttons
function setupOrderItemClickDelegation() {
    const orderItemsDiv = document.getElementById('order-items');
    if (!orderItemsDiv) return;

    orderItemsDiv.addEventListener('click', (event) => {
        const removeBtn = event.target.closest('[data-remove-id]');
        if (removeBtn) {
            event.stopPropagation();
            const id = Number(removeBtn.dataset.removeId);
            removeFromOrder(event, id);
            return;
        }

        const card = event.target.closest('.order-item');
        if (card) {
            const id = Number(card.dataset.orderId);
            viewOrderItem(id);
        }
    });
}

// Highlight the currently active order card
function highlightActiveOrderItem() {
    const orderItemsDiv = document.getElementById('order-items');
    if (!orderItemsDiv) return;
    orderItemsDiv.querySelectorAll('.order-item').forEach(card => {
        const id = Number(card.dataset.orderId);
        if (id === activeSelectionId) {
            card.classList.add('order-item--active');
        } else {
            card.classList.remove('order-item--active');
        }
    });
}

// Apply a saved item's selections to the current view and state
function applyItemSelections(item) {
    resetSelection();
    const activeView = document.querySelector('.category-view.active');
    if (!activeView) return;

    const sideCards = Array.from(activeView.querySelectorAll('.side-card'));
    const entreeCards = Array.from(activeView.querySelectorAll('.entree-card'));

    const setCardQty = (card, qty) => {
        card.dataset.qty = String(qty);
        const badge = card.querySelector('.meal-qty-card__count');
        if (badge) {
            badge.textContent = qty;
            const show = qty > 0;
            badge.hidden = !show;
            badge.style.display = show ? 'flex' : 'none';
        }
        card.classList.toggle('selected', qty > 0);
    };

    // clear all card quantities first
    sideCards.forEach(card => setCardQty(card, 0));
    entreeCards.forEach(card => setCardQty(card, 0));

    // count desired quantities from the order item
    const sideCounts = {};
    const entreeCounts = {};
    const otherRecipes = [];
    item.recipes.forEach(recipe => {
        const type = (recipe.type || '').toLowerCase();
        if (type === 'side') {
            sideCounts[recipe.id] = (sideCounts[recipe.id] || 0) + 1;
        } else if (type === 'entree' || type === 'entrée') {
            entreeCounts[recipe.id] = (entreeCounts[recipe.id] || 0) + 1;
        } else {
            otherRecipes.push(recipe);
        }
    });

    // apply side counts (max 1 per card, total 2)
    let sideTotal = 0;
    sideCards.forEach(card => {
        const id = card.dataset.recipeId;
        let qty = Math.min(sideCounts[id] || 0, 1);
        if (sideTotal + qty > 2) qty = Math.max(0, 2 - sideTotal);
        sideTotal += qty;
        setCardQty(card, qty);
        if (qty > 0) {
            const isHalf = sideTotal === 2;
            for (let i = 0; i < qty; i += 1) {
                currentSelection.sides.push({
                    id: card.dataset.recipeId,
                    name: card.dataset.recipeName,
                    type: card.dataset.recipeType,
                    price: parseFloat(card.dataset.recipePrice) || 0,
                    isHalf,
                });
            }
        }
    });

    // apply entree counts with category limit
    const maxEntrees = item.category === 'plate' ? 2 : item.category === 'bigger-plate' ? 3 : 1;
    let entreeTotal = 0;
    entreeCards.forEach(card => {
        const id = card.dataset.recipeId;
        let qty = entreeCounts[id] || 0;
        if (entreeTotal + qty > maxEntrees) qty = Math.max(0, maxEntrees - entreeTotal);
        entreeTotal += qty;
        setCardQty(card, qty);
        for (let i = 0; i < qty; i += 1) {
            currentSelection.entrees.push({
                id: card.dataset.recipeId,
                name: card.dataset.recipeName,
                type: card.dataset.recipeType,
                price: parseFloat(card.dataset.recipePrice) || 0,
            });
        }
    });

    // update counters
    const sideContainer = activeView.querySelector('.cashier-selection-grid--sides');
    const entreeContainer = activeView.querySelector('.cashier-selection-grid--entrees');
    if (sideContainer) updateCountIndicator(sideContainer.id, sideTotal, 2);
    if (entreeContainer) updateCountIndicator(entreeContainer.id, entreeTotal, maxEntrees);

    // handle single-selection categories (drinks/appetizers/a la carte)
    if (['a-la-carte', 'appetizers', 'drinks'].includes(item.category)) {
        const first = otherRecipes[0];
        if (first) {
            activeView.querySelectorAll('.alacarte-btn, .appetizer-btn, .drink-btn').forEach(b => b.classList.remove('selected'));
            const btn = activeView.querySelector(`[data-recipe-id="${first.id}"]`);
            if (btn) btn.classList.add('selected');
            currentSelection.recipes = [first];
            // restore size if present
            if (item.category === 'a-la-carte') {
                const size = first.size || 'M';
                const input = document.querySelector(`input[name="alacarte-size"][value="${size}"]`);
                if (input) input.checked = true;
            } else if (item.category === 'appetizers') {
                const size = first.size || 'M';
                const input = document.querySelector(`input[name="appetizer-size"][value="${size}"]`);
                if (input) input.checked = true;
            } else if (item.category === 'drinks') {
                const size = first.size || 'M';
                const input = document.querySelector(`input[name="drink-size"][value="${size}"]`);
                if (input) input.checked = true;
            }
        }
    }

    updateActiveOrderItemFromSelection();
}

function buildCurrentRecipes() {
    return [
        ...currentSelection.sides,
        ...currentSelection.entrees,
        ...currentSelection.recipes
    ];
}

// When editing an order item, keep the order data in sync with currentSelection
function updateActiveOrderItemFromSelection() {
    if (activeSelectionId === null) return;
    const item = currentOrder.find(o => o.id === activeSelectionId);
    if (!item) return;

    // If selection was cleared while editing, fall back to the saved snapshot instead of erasing the item
    if (isSelectionEmpty(currentSelection) && activeSelectionSnapshot && activeSelectionSnapshot.id === item.id) {
        item.recipes = JSON.parse(JSON.stringify(activeSelectionSnapshot.recipes || []));
        item.price = computePriceForCategory(item.category, item.recipes);
    } else {
        item.recipes = buildCurrentRecipes();
        item.price = computePriceForCategory(item.category, item.recipes);
        // refresh snapshot with latest valid selection
        activeSelectionSnapshot = {
            id: item.id,
            category: item.category,
            menuItemName: item.menuItemName,
            recipes: JSON.parse(JSON.stringify(item.recipes || [])),
            price: item.price
        };
    }
    updateOrderDisplay();
    highlightActiveOrderItem();
}

function isSelectionEmpty(selection) {
    return (
        (!selection.sides || selection.sides.length === 0) &&
        (!selection.entrees || selection.entrees.length === 0) &&
        (!selection.recipes || selection.recipes.length === 0)
    );
}

function restoreActiveSelectionFromSnapshot() {
    if (!activeSelectionSnapshot) return;
    const item = currentOrder.find(o => o.id === activeSelectionSnapshot.id);
    if (!item) return;
    item.recipes = JSON.parse(JSON.stringify(activeSelectionSnapshot.recipes || []));
    item.price = activeSelectionSnapshot.price;
    updateOrderDisplay();
    highlightActiveOrderItem();
}

function computePriceForCategory(category, recipesOverride) {
    const recipes = recipesOverride || buildCurrentRecipes();
    let price = 0;
    if (category === 'bowl') {
        price = 8.30;
        recipes.filter(r => r.type?.toLowerCase() === 'entree' || r.type?.toLowerCase() === 'entrée')
            .forEach(entree => { price += entree.price; });
    } else if (category === 'plate') {
        price = 12.15;
        recipes.filter(r => r.type?.toLowerCase() === 'entree' || r.type?.toLowerCase() === 'entrée')
            .forEach(entree => { price += entree.price; });
    } else if (category === 'bigger-plate') {
        price = 14.05;
        recipes.filter(r => r.type?.toLowerCase() === 'entree' || r.type?.toLowerCase() === 'entrée')
            .forEach(entree => { price += entree.price; });
    } else if (category === 'a-la-carte') {
        recipes.forEach(recipe => {
            const size = recipe.size || 'M';
            const isPremium = cashierPriceMaps.alacartePremiumItems.has(recipe.name);
            const map = cashierPriceMaps.alacartePrices[recipe.name] || (isPremium ? cashierPriceMaps.alacartePremiumPrices : cashierPriceMaps.alacarteSizePrices);
            const p = (map && map[size]) || 0;
            price += p;
        });
    } else if (category === 'appetizers') {
        recipes.forEach(recipe => {
            const size = recipe.size || 'M';
            const map = cashierPriceMaps.appetizerPrices[recipe.name] || {};
            price += map[size] || 0;
        });
    } else if (category === 'drinks') {
        recipes.forEach(recipe => {
            const size = recipe.size || 'M';
            const map = cashierPriceMaps.drinkPrices[recipe.name] || {};
            const hasSizes = cashierPriceMaps.drinkHasSizes[recipe.name];
            const p = hasSizes ? (map[size] || map['M'] || 0) : (cashierPriceMaps.drinkSingle[recipe.name] || map['M'] || 0);
            price += p;
        });
    }
    return price;
}

// Clear all selection button states (visual)
function clearSelectionButtons() {
    document.querySelectorAll('.selection-btn').forEach(btn => {
        btn.classList.remove('selected');
        btn.classList.remove('active');
        const badge = btn.querySelector('.selection-badge');
        if (badge && !badge.classList.contains('meal-qty-card__count')) badge.remove();
    });
    // Reset quantity cards/indicators as well
    clearQtyCards();
}

function setupClearOrderModal() {
    const clearBtn = document.getElementById('clear-btn');
    if (clearBtn && clearConfirmModal && confirmClearBtn && cancelClearBtn) {
        clearBtn.addEventListener('click', (e) => {
            e.preventDefault();
            showClearModal();
        });
        confirmClearBtn.addEventListener('click', () => {
            hideClearModal();
            activeSelectionId = null;
            resetCashierInterface();
        });
        cancelClearBtn.addEventListener('click', hideClearModal);
        clearConfirmModal.addEventListener('click', (e) => {
            if (e.target === clearConfirmModal) hideClearModal();
        });
    }
}

function showClearModal() {
    clearConfirmModal.classList.add('show');
    clearConfirmModal.setAttribute('aria-hidden', 'false');
}

function hideClearModal() {
    clearConfirmModal.classList.remove('show');
    clearConfirmModal.setAttribute('aria-hidden', 'true');
}

function showCashierWarning(message) {
    if (!warningBanner) return;
    warningBanner.textContent = message;
    warningBanner.classList.add('show');
    if (warningTimer) clearTimeout(warningTimer);
    warningTimer = setTimeout(() => {
        warningBanner.classList.remove('show');
    }, 1800);
}

// Update totals
function updateTotals() {
    const subtotal = currentOrder.reduce((sum, item) => sum + item.price, 0);
    const tax = subtotal * 0.0825;
    const total = subtotal + tax;

    document.getElementById('subtotal').textContent = `$${subtotal.toFixed(2)}`;
    document.getElementById('tax').textContent = `$${tax.toFixed(2)}`;
    document.getElementById('total').textContent = `$${total.toFixed(2)}`;
}

function showPurchaseSuccessModal(orderNumber, total) {
    if (!purchaseModal) return;
    if (purchaseModalNumberEl) {
        purchaseModalNumberEl.textContent = orderNumber;
    }
    if (purchaseModalTotalEl) {
        purchaseModalTotalEl.textContent = `$${total.toFixed(2)}`;
    }
    purchaseModal.classList.add('show');
    purchaseModal.setAttribute('aria-hidden', 'false');
}

function hidePurchaseModal() {
    if (!purchaseModal) return;
    purchaseModal.classList.remove('show');
    purchaseModal.setAttribute('aria-hidden', 'true');
}

function resetCashierInterface() {
    currentOrder = [];
    updateOrderDisplay();
}

// Checkout
document.getElementById('checkout-btn').addEventListener('click', function() {
    if (currentOrder.length === 0) {
        alert('Please add items to the order first.');
        return;
    }
    
    // Calculate total
    const subtotal = currentOrder.reduce((sum, item) => sum + item.price, 0);
    const tax = subtotal * 0.0825;
    const total = subtotal + tax;
    
    // Prepare order data
    const orderData = {
        orderItems: currentOrder,
        totalPrice: total
    };
    
    // Send to server
    fetch('/cashierInterface/create-order/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const orderNumber = data.order_id || `POS-${completedOrderCounter++}`;
            showPurchaseSuccessModal(orderNumber, total);
        } else {
            alert('Error creating order: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to complete order. Please try again.');
    });
});
