(() => {
  const orders = [];
  let internalId = 1;
  let currentView = 'active';
  const pageByView = { active: 0, completed: 0 };
  const MAX_DISPLAY = 5;

  function loadInitialOrders() {
    
    const script = document.getElementById('recent-orders-data');
    if (!script) console.log("no missed orders (or error)");
    let data;
    //console.log(script.textContent);
    try {
      data = JSON.parse(script.textContent);
    } catch (error) {
      console.log("Error parsing recent orders data:", error);
      data = [];
    }
    if (Array.isArray(data)) {
      data.forEach(orderData => addOrder(orderData));
    }
  }

  function normalizeStatus(status) {
    const value = status === undefined || status === null ? '' : String(status).toLowerCase();
    if (!value) return 'pending';
    if (['done', 'completed', 'complete', 'ready', 'fulfilled'].includes(value)) return 'completed';
    if (['cancelled', 'canceled'].includes(value)) return 'cancelled';
    return value;
  }

  function isCompleted(status) {
    const normalized = normalizeStatus(status);
    return normalized === 'completed';
  }

  function formatStatus(status) {
    const normalized = normalizeStatus(status);
    return normalized.replace(/\b\w/g, c => c.toUpperCase()) || 'Pending';
  }

  function extractItems(order) {
    const items = [];
    //console.log('Extracting items from order:', order);
    if (order && Array.isArray(order.items)) {
      order.items.forEach(it => {
        if (!it) return;
        if (it.category === 'meal') {
          const mealType = it.meal_type || it.meal_name || 'Meal';
          const header = mealType;
          const parts = [];
          const entrees = Array.isArray(it.entrees) ? it.entrees : [];


          entrees.forEach(e => {
            if (!e) return;
            if (typeof e === 'string') {
              parts.push(e);
            } else if (typeof e === 'object') {
              const name = e.name || e.meal_name || e.title || 'Item';
              const qty = e.qty ?? e.quantity ?? e.count;
              parts.push(qty ? `${name} x${qty}` : name);
            } else {
              parts.push(String(e));
            }
          });

          // side can be an array, an object, or a simple string
          if (Array.isArray(it.side)) {
            it.side.forEach(s => {
              if (!s) return;
              if (typeof s === 'string') parts.push(s);
              else if (typeof s === 'object') parts.push(s.name || s.title || JSON.stringify(s));
              else parts.push(String(s));
            });
          } else if (it.side) {
            if (typeof it.side === 'string') parts.push(it.side);
            else if (typeof it.side === 'object') parts.push(it.side.name || it.side.title || JSON.stringify(it.side));
            else parts.push(String(it.side));
          }

          if (parts.length) {
            items.push({ title: header, lines: parts });
          } else {
            items.push({ title: header, lines: ['No details available'] });
          }
        } else {
          const name = it.name || it.meal_name || it.category || 'Item';
          const size = it.size ? ` (${it.size})` : '';
          const title = `${name}${size}`;
          items.push({ title, lines: [] });
        }
      });
    }
    if (!items.length) {
      items.push({ title: 'Order', lines: ['No details available'] });
    }
    return items;
  }

  function addOrder(data) {
    const id = data.order_id || data.id || internalId++;
    const status = normalizeStatus(data.status);
    orders.unshift({ id, items: extractItems(data), status });
    render();
  }

  function toggleStatus(id) {
    const order = orders.find(o => o.id === id);
    if (!order) return;
    const newStatus = (order.status === 'completed') ? 'pending' : 'completed';
    // optimistic UI could be applied, but persist on server first
    updateOrderStatus(id, newStatus).then(success => {
      if (success) {
        order.status = normalizeStatus(newStatus);
        render();
      } else {
        console.error('Failed to update order status for', id);
      }
    });
  }

  function getCookie(name) {
    const v = document.cookie.split('; ').find(row => row.startsWith(name + '='));
    return v ? decodeURIComponent(v.split('=')[1]) : null;
  }

  function updateOrderStatus(id, status) {
    const url = `/kitchen/api/orders/${id}/status/`;
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify({ status })
    })
      .then(res => {
        if (!res.ok) throw new Error('Network response was not ok');
        return res.json();
      })
      .then(data => data && data.success === true)
      .catch(err => {
        console.error('updateOrderStatus error', err);
        return false;
      });
  }

  function updateToggleStates() {
    document.querySelectorAll('.kitchen-toggle').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.target === currentView);
    });
  }

  function render() {
    const container = document.getElementById('kitchen-orders');
    const wrap = document.querySelector('.kitchen-orders-wrap');
    const pager = document.getElementById('kitchen-pagination');
    if (!container) return;
    container.innerHTML = '';

    const filteredOrders = orders.filter(order =>
      currentView === 'active' ? !isCompleted(order.status) : isCompleted(order.status)
    );

    if (wrap) wrap.classList.toggle('has-orders', filteredOrders.length > 0);
    container.classList.toggle('has-orders', filteredOrders.length > 0);
    if (pager) pager.style.display = 'flex';

    if (filteredOrders.length === 0) {
      updatePager(0, 0);
      return;
    }

    const totalPages = Math.ceil(filteredOrders.length / MAX_DISPLAY) || 1;
    const currentPage = Math.min(pageByView[currentView] || 0, totalPages - 1);
    pageByView[currentView] = currentPage;

    const start = currentPage * MAX_DISPLAY;
    const pageOrders = filteredOrders.slice(start, start + MAX_DISPLAY);

    pageOrders.forEach(order => {
      const button = document.createElement('button');
      button.className = 'kitchen-mark-complete-btn';
      button.textContent = (order.status === 'completed') ? 'Mark Incomplete' : 'Mark Complete';
      button.addEventListener('click', () => toggleStatus(order.id));

      const card = document.createElement('article');
      card.className = 'order-card kitchen-order-card';

      const header = document.createElement('header');
      header.className = 'order-card__header';

      const title = document.createElement('span');
      title.className = 'kitchen-order-title';
      title.textContent = `Order #${order.id ?? '—'}`;
      header.appendChild(title);

      const statusPill = document.createElement('span');
      const normalizedStatus = normalizeStatus(order.status);
      statusPill.className = `kitchen-order-status kitchen-order-status--${normalizedStatus}`;
      statusPill.textContent = formatStatus(order.status);
      header.appendChild(statusPill);

      card.appendChild(header);
      card.appendChild(button);

      const body = document.createElement('div');
      body.className = 'order-card__body';
      const list = document.createElement('ul');
      list.className = 'kitchen-order-list';

      order.items.forEach(group => {
        const parentLi = document.createElement('li');
        parentLi.textContent = group.title || 'Item';

        if (group.lines && group.lines.length) {
          const subList = document.createElement('ul');
          subList.className = 'kitchen-order-sublist';
          group.lines.forEach(line => {
            const subLi = document.createElement('li');
            subLi.textContent = line;
            subList.appendChild(subLi);
          });
          parentLi.appendChild(subList);
        }

        list.appendChild(parentLi);
      });

      body.appendChild(list);
      card.appendChild(body);

      container.appendChild(card);
    });

    updatePager(currentPage, totalPages);
  }

  function setupToggleButtons() {
    document.querySelectorAll('.kitchen-toggle').forEach(btn => {
      btn.addEventListener('click', () => {
        currentView = btn.dataset.target;
        pageByView[currentView] = pageByView[currentView] || 0;
        updateToggleStates();
        render();
      });
    });
  }

  function setupPagination() {
    const prev = document.getElementById('kitchen-prev');
    const next = document.getElementById('kitchen-next');
    if (prev) prev.addEventListener('click', () => changePage(-1));
    if (next) next.addEventListener('click', () => changePage(1));
  }

  function changePage(delta) {
    const filteredOrders = orders.filter(order =>
      currentView === 'active' ? !isCompleted(order.status) : isCompleted(order.status)
    );
    const totalPages = Math.ceil(filteredOrders.length / MAX_DISPLAY);
    if (totalPages <= 1) return;
    const nextPage = Math.min(Math.max((pageByView[currentView] || 0) + delta, 0), totalPages - 1);
    pageByView[currentView] = nextPage;
    render();
  }

  function updatePager(currentPage, totalPages) {
    const indicator = document.getElementById('kitchen-page-indicator');
    const prev = document.getElementById('kitchen-prev');
    const next = document.getElementById('kitchen-next');
    if (indicator) {
      indicator.textContent = totalPages > 0 ? `Page ${currentPage + 1} of ${totalPages}` : 'Page 0 of 0';
    }
    if (prev) prev.disabled = currentPage <= 0 || totalPages <= 1;
    if (next) next.disabled = currentPage >= totalPages - 1 || totalPages <= 1;
  }

  function setupWebSocket() {
    //console.log("setting up ws");
    try {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws';
      const url = `${proto}://${location.host}/ws/orders/`;
      const ws = new WebSocket(url);
      ws.onmessage = (e) => {
        let data;
        try { data = JSON.parse(e.data); }
        catch { data = { items: [{ name: String(e.data) }] }; }
        //console.log('received websocket msg', data); 
        if (data.low_stock_items) {
          console.log('Low stock alert:', data.low_stock_items);
          lowStockAlert(data.low_stock_items);
        } else {
          console.log('New order received:', data);
          addOrder(data);
        }
      };
      ws.onopen = () => console.log('Kitchen WebSocket connected');
      ws.onclose = () => console.warn('Kitchen WebSocket closed');
      ws.onerror = (err) => console.error('Kitchen WebSocket error:', err);
    } catch (e) {
      console.warn('WebSocket not available; running without real-time updates', e);
    }
  }

  // takes an array of strings 
  function lowStockAlert(items) {
    const arr = Array.isArray(items) ? items.filter(Boolean).map(String) : [];
    if (!arr.length) return;
    let container = document.querySelector('.low-stock-alert-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'low-stock-alert-container';
      document.body.appendChild(container);
    }
    const alertEl = document.createElement('div');
    alertEl.className = 'low-stock-alert';
    alertEl.textContent = 'Low stock: ' + arr.join(', ');
    container.appendChild(alertEl);
    // auto fade then remove
    setTimeout(() => {
      alertEl.classList.add('fade-out');
      alertEl.addEventListener('transitionend', () => alertEl.remove(), { once: true });
    }, 8000);
  }

  function init() {
    setupToggleButtons();
    setupPagination();
    updateToggleStates();
    loadInitialOrders();
    setupWebSocket();
    render();
  }

  document.addEventListener('DOMContentLoaded', init);
})();
