<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import {
  api,
  apiDelete,
  apiGet,
  apiPatch,
  apiPost,
  clearAuth,
  loadAuth,
  saveAuth,
} from "./api";

const statusMessage = ref("");
const errorMessage = ref("");
const loading = ref(false);

const authForm = reactive(loadAuth());
const me = ref(null);

const activeTab = ref("dashboard");

const stores = ref([]);
const departments = ref([]);
const products = ref([]);
const supplierBases = ref([]);
const baseStocks = ref([]);
const departmentStocks = ref([]);
const purchaseOrders = ref([]);
const sales = ref([]);

const selectedStoreId = ref("");

const dashboard = reactive({
  storeProducts: [],
  missingProducts: [],
  departmentValues: [],
  managers: [],
  productBases: [],
  productSearch: "",
});

const productForm = reactive({
  name: "",
  unit: "PCS",
  preferred_base: "",
  description: "",
});

const departmentForm = reactive({
  store: "",
  name: "",
  manager: "",
});

const moveStockForm = reactive({
  source_department: "",
  target_department: "",
  product: "",
  grade: "",
  quantity: 1,
});

const priceForm = reactive({
  department_stock_id: "",
  retail_price: "",
});

const purchaseForm = reactive({
  store: "",
  supplier_base: "",
  department: "",
  notes: "",
  items: [
    {
      product: "",
      grade: "",
      quantity: 1,
      purchase_price: "",
    },
  ],
});

const saleForm = reactive({
  store: "",
  department: "",
  notes: "",
  items: [
    {
      product: "",
      grade: "",
      quantity: 1,
      retail_price: "",
    },
  ],
});

const reportForm = reactive({
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1,
});

const monthlyReport = ref(null);
const managersCatalog = ref([]);

const isAdmin = computed(() => !!me.value?.is_admin);

function unwrapList(data) {
  if (Array.isArray(data)) return data;
  if (data && Array.isArray(data.results)) return data.results;
  return [];
}

function setMessage(message) {
  statusMessage.value = message;
  errorMessage.value = "";
}

function setError(err) {
  statusMessage.value = "";
  errorMessage.value = err?.response?.data?.detail || err.message || "Ошибка запроса";
}

async function login() {
  if (!authForm.username || !authForm.password) {
    errorMessage.value = "Введите логин и пароль.";
    return;
  }

  saveAuth(authForm);
  await bootstrap();
}

function logout() {
  clearAuth();
  me.value = null;
  statusMessage.value = "";
  errorMessage.value = "";
}

async function bootstrap() {
  loading.value = true;
  try {
    const [meData, storesData, departmentsData, productsData, basesData, baseStockData, depStockData, purchaseData, salesData, managersData] =
      await Promise.all([
        apiGet("/api/me/"),
        apiGet("/api/stores/"),
        apiGet("/api/departments/"),
        apiGet("/api/products/"),
        apiGet("/api/supplier-bases/"),
        apiGet("/api/base-stocks/"),
        apiGet("/api/department-stocks/"),
        apiGet("/api/purchase-orders/"),
        apiGet("/api/sales/"),
        apiGet("/api/managers-catalog/"),
      ]);

    me.value = meData;
    stores.value = unwrapList(storesData);
    departments.value = unwrapList(departmentsData);
    products.value = unwrapList(productsData);
    supplierBases.value = unwrapList(basesData);
    baseStocks.value = unwrapList(baseStockData);
    departmentStocks.value = unwrapList(depStockData);
    purchaseOrders.value = unwrapList(purchaseData);
    sales.value = unwrapList(salesData);
    managersCatalog.value = unwrapList(managersData);

    if (!selectedStoreId.value && stores.value.length > 0) {
      selectedStoreId.value = String(stores.value[0].id);
    }

    purchaseForm.store = selectedStoreId.value;
    saleForm.store = selectedStoreId.value;

    await loadDashboard();
    setMessage("Данные загружены");
  } catch (err) {
    setError(err);
  } finally {
    loading.value = false;
  }
}

async function refreshLists() {
  await bootstrap();
}

async function loadDashboard() {
  if (!selectedStoreId.value) return;

  try {
    const [storeProductsData, missingData, valuesData, managersData] = await Promise.all([
      apiGet("/api/dashboard/store-products/", { store_id: selectedStoreId.value }),
      apiGet("/api/dashboard/missing-products/", { store_id: selectedStoreId.value }),
      apiGet("/api/dashboard/department-values/", { store_id: selectedStoreId.value }),
      apiGet("/api/dashboard/managers/", { store_id: selectedStoreId.value }),
    ]);

    dashboard.storeProducts = unwrapList(storeProductsData);
    dashboard.missingProducts = unwrapList(missingData);
    dashboard.departmentValues = unwrapList(valuesData);
    dashboard.managers = unwrapList(managersData);
  } catch (err) {
    setError(err);
  }
}

async function findProductBases() {
  if (!dashboard.productSearch.trim()) {
    errorMessage.value = "Введите название товара для поиска.";
    return;
  }
  try {
    const data = await apiGet("/api/dashboard/product-bases/", {
      product_name: dashboard.productSearch,
    });
    dashboard.productBases = unwrapList(data);
  } catch (err) {
    setError(err);
  }
}

async function createProduct() {
  if (!productForm.name.trim()) {
    errorMessage.value = "Название товара обязательно.";
    return;
  }

  try {
    await apiPost("/api/products/", {
      name: productForm.name,
      unit: productForm.unit,
      preferred_base: productForm.preferred_base || null,
      description: productForm.description,
    });
    setMessage("Товар добавлен");
    productForm.name = "";
    productForm.description = "";
    await refreshLists();
  } catch (err) {
    setError(err);
  }
}

async function deleteProduct(id) {
  if (!confirm("Удалить товар?")) return;
  try {
    await apiDelete(`/api/products/${id}/`);
    setMessage("Товар удален");
    await refreshLists();
  } catch (err) {
    setError(err);
  }
}

async function createDepartment() {
  if (!departmentForm.store || !departmentForm.name.trim()) {
    errorMessage.value = "Для отдела нужны магазин и название.";
    return;
  }

  try {
    await apiPost("/api/departments/", {
      store: departmentForm.store,
      name: departmentForm.name,
      manager: departmentForm.manager || null,
      is_open: true,
    });
    setMessage("Отдел создан");
    departmentForm.name = "";
    await refreshLists();
  } catch (err) {
    setError(err);
  }
}

async function toggleDepartment(dep, openFlag) {
  try {
    const action = openFlag ? "open" : "close";
    await apiPost(`/api/departments/${dep.id}/${action}/`);
    setMessage(openFlag ? "Отдел открыт" : "Отдел закрыт");
    await refreshLists();
  } catch (err) {
    setError(err);
  }
}

async function moveStock() {
  if (!moveStockForm.source_department || !moveStockForm.target_department || !moveStockForm.product || !moveStockForm.grade.trim()) {
    errorMessage.value = "Заполни все поля перемещения товара.";
    return;
  }

  if (Number(moveStockForm.quantity) <= 0) {
    errorMessage.value = "Количество должно быть больше 0.";
    return;
  }

  try {
    await apiPost(`/api/departments/${moveStockForm.source_department}/move_stock/`, {
      target_department: moveStockForm.target_department,
      product: moveStockForm.product,
      grade: moveStockForm.grade,
      quantity: Number(moveStockForm.quantity),
    });
    setMessage("Товар перемещен");
    await refreshLists();
  } catch (err) {
    setError(err);
  }
}

async function changeRetailPrice() {
  if (!priceForm.department_stock_id || Number(priceForm.retail_price) <= 0) {
    errorMessage.value = "Выбери остаток и укажи цену больше 0.";
    return;
  }

  try {
    await apiPatch(`/api/department-stocks/${priceForm.department_stock_id}/`, {
      retail_price: Number(priceForm.retail_price),
    });
    setMessage("Розничная цена обновлена");
    await refreshLists();
  } catch (err) {
    setError(err);
  }
}

function addPurchaseItem() {
  purchaseForm.items.push({ product: "", grade: "", quantity: 1, purchase_price: "" });
}

function removePurchaseItem(index) {
  purchaseForm.items.splice(index, 1);
}

async function createPurchaseOrder() {
  if (!purchaseForm.store || !purchaseForm.supplier_base || !purchaseForm.department || purchaseForm.items.length === 0) {
    errorMessage.value = "Заполни магазин, базу, отдел и позиции закупки.";
    return;
  }

  try {
    await apiPost("/api/purchase-orders/", {
      store: Number(purchaseForm.store),
      supplier_base: Number(purchaseForm.supplier_base),
      department: Number(purchaseForm.department),
      notes: purchaseForm.notes,
      status: "DRAFT",
      items: purchaseForm.items.map((item) => ({
        product: Number(item.product),
        grade: item.grade,
        quantity: Number(item.quantity),
        purchase_price: Number(item.purchase_price),
      })),
    });
    setMessage("Закупка создана");
    purchaseForm.items = [{ product: "", grade: "", quantity: 1, purchase_price: "" }];
    await refreshLists();
  } catch (err) {
    setError(err);
  }
}

async function receivePurchase(orderId) {
  try {
    await apiPost(`/api/purchase-orders/${orderId}/receive/`);
    setMessage("Закупка оприходована");
    await refreshLists();
  } catch (err) {
    setError(err);
  }
}

async function downloadPurchaseDocument(orderId) {
  try {
    const response = await api.get(`/api/purchase-orders/${orderId}/document/`, {
      responseType: "blob",
    });
    const fileURL = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = fileURL;
    link.setAttribute("download", `purchase_order_${orderId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (err) {
    setError(err);
  }
}

function addSaleItem() {
  saleForm.items.push({ product: "", grade: "", quantity: 1, retail_price: "" });
}

function removeSaleItem(index) {
  saleForm.items.splice(index, 1);
}

async function createSale() {
  if (!saleForm.store || !saleForm.department || saleForm.items.length === 0) {
    errorMessage.value = "Заполни магазин, отдел и позиции продажи.";
    return;
  }

  try {
    await apiPost("/api/sales/", {
      store: Number(saleForm.store),
      department: Number(saleForm.department),
      notes: saleForm.notes,
      items: saleForm.items.map((item) => ({
        product: Number(item.product),
        grade: item.grade,
        quantity: Number(item.quantity),
        retail_price: Number(item.retail_price),
      })),
    });
    setMessage("Продажа проведена");
    saleForm.items = [{ product: "", grade: "", quantity: 1, retail_price: "" }];
    await refreshLists();
  } catch (err) {
    setError(err);
  }
}

async function loadMonthlyReport() {
  if (!selectedStoreId.value) {
    errorMessage.value = "Выбери магазин для отчета.";
    return;
  }

  try {
    const data = await apiGet("/api/reports/monthly/", {
      store_id: selectedStoreId.value,
      year: reportForm.year,
      month: reportForm.month,
    });
    monthlyReport.value = data;
    setMessage("Ежемесячный отчет сформирован");
  } catch (err) {
    setError(err);
  }
}

onMounted(async () => {
  if (authForm.username && authForm.password) {
    await bootstrap();
  }
});
</script>

<template>
  <div class="page">
    <header class="hero" aria-label="Шапка приложения">
      <h1>АСУ «Магазин»</h1>
      <p>Управление товарами, закупками, отделами и отчетами</p>
    </header>

    <section class="panel" aria-label="Авторизация">
      <div v-if="!me" class="login-grid">
        <label>
          Логин
          <input v-model.trim="authForm.username" type="text" required autocomplete="username" />
        </label>
        <label>
          Пароль
          <input v-model="authForm.password" type="password" required autocomplete="current-password" />
        </label>
        <button @click="login" :disabled="loading">Войти</button>
      </div>

      <div v-else class="user-line">
        <span>Пользователь: <strong>{{ me.username }}</strong> ({{ isAdmin ? "admin" : "user" }})</span>
        <button @click="logout">Выйти</button>
      </div>

      <p v-if="statusMessage" class="ok-msg">{{ statusMessage }}</p>
      <p v-if="errorMessage" class="error-msg">{{ errorMessage }}</p>
    </section>

    <main v-if="me" class="main-layout">
      <section class="panel filter-row" aria-label="Фильтр магазина">
        <label>
          Магазин
          <select v-model="selectedStoreId" @change="loadDashboard">
            <option v-for="store in stores" :key="store.id" :value="String(store.id)">{{ store.name }} ({{ store.number }})</option>
          </select>
        </label>
      </section>

      <nav class="tabs" aria-label="Разделы">
        <button :class="{ active: activeTab === 'dashboard' }" @click="activeTab = 'dashboard'">Дашборд</button>
        <button :class="{ active: activeTab === 'catalog' }" @click="activeTab = 'catalog'">Справочники</button>
        <button :class="{ active: activeTab === 'operations' }" @click="activeTab = 'operations'">Операции</button>
        <button :class="{ active: activeTab === 'report' }" @click="activeTab = 'report'">Отчет</button>
      </nav>

      <section v-if="activeTab === 'dashboard'" class="grid-2">
        <article class="panel">
          <h2>Товары в магазине</h2>
          <ul>
            <li v-for="item in dashboard.storeProducts" :key="`${item.product_id}-${item.grade}`">
              {{ item.product__name }} ({{ item.grade }}): {{ item.total_quantity }}
            </li>
          </ul>
        </article>

        <article class="panel">
          <h2>Отсутствующие товары (что заказать)</h2>
          <ul>
            <li v-for="item in dashboard.missingProducts" :key="item.product_id">
              {{ item.product_name }}: {{ item.options.length ? item.options.map((o) => `${o.base_name} (${o.quantity})`).join(', ') : 'нет на базах' }}
            </li>
          </ul>
        </article>

        <article class="panel">
          <h2>Суммарная стоимость по отделам</h2>
          <ul>
            <li v-for="row in dashboard.departmentValues" :key="row.department_id">
              {{ row.department_name }}: {{ row.total_value }} руб.
            </li>
          </ul>
        </article>

        <article class="panel">
          <h2>Заведующие отделами</h2>
          <ul>
            <li v-for="row in dashboard.managers" :key="row.department_id">
              {{ row.department_name }}: {{ row.manager_username || 'не назначен' }}
            </li>
          </ul>
        </article>

        <article class="panel wide">
          <h2>Наличие товара на базах</h2>
          <div class="inline-form">
            <input v-model.trim="dashboard.productSearch" placeholder="Введите название товара" />
            <button @click="findProductBases">Найти</button>
          </div>
          <ul>
            <li v-for="(row, index) in dashboard.productBases" :key="index">
              {{ row.product_name }} | {{ row.base_name }} | {{ row.grade }} | {{ row.quantity }}
            </li>
          </ul>
        </article>
      </section>

      <section v-if="activeTab === 'catalog'" class="grid-2">
        <article class="panel">
          <h2>Товары</h2>
          <form class="stack" @submit.prevent="createProduct">
            <input v-model.trim="productForm.name" placeholder="Название" required />
            <select v-model="productForm.unit">
              <option value="PCS">шт</option>
              <option value="KG">кг</option>
              <option value="L">л</option>
              <option value="PACK">упак</option>
            </select>
            <select v-model="productForm.preferred_base">
              <option value="">Предпочтительная база</option>
              <option v-for="base in supplierBases" :key="base.id" :value="base.id">{{ base.name }}</option>
            </select>
            <textarea v-model="productForm.description" placeholder="Описание"></textarea>
            <button :disabled="!isAdmin">Добавить товар</button>
          </form>

          <ul>
            <li v-for="product in products" :key="product.id">
              {{ product.name }} ({{ product.unit }})
              <button v-if="isAdmin" @click="deleteProduct(product.id)">Удалить</button>
            </li>
          </ul>
        </article>

        <article class="panel">
          <h2>Отделы: открыть/закрыть</h2>
          <form class="stack" @submit.prevent="createDepartment">
            <select v-model="departmentForm.store" required>
              <option value="">Выбери магазин</option>
              <option v-for="store in stores" :key="store.id" :value="store.id">{{ store.name }}</option>
            </select>
            <input v-model.trim="departmentForm.name" required placeholder="Название отдела" />
            <select v-model="departmentForm.manager">
              <option value="">Заведующий</option>
              <option v-for="manager in managersCatalog" :key="manager.id" :value="manager.id">{{ manager.username }}</option>
            </select>
            <button :disabled="!isAdmin">Создать отдел</button>
          </form>

          <ul>
            <li v-for="dep in departments" :key="dep.id">
              {{ dep.name }} ({{ dep.is_open ? 'открыт' : 'закрыт' }})
              <button v-if="isAdmin && dep.is_open" @click="toggleDepartment(dep, false)">Закрыть</button>
              <button v-if="isAdmin && !dep.is_open" @click="toggleDepartment(dep, true)">Открыть</button>
            </li>
          </ul>
        </article>

        <article class="panel">
          <h2>Перемещение товара</h2>
          <form class="stack" @submit.prevent="moveStock">
            <select v-model="moveStockForm.source_department" required>
              <option value="">Откуда</option>
              <option v-for="dep in departments" :key="dep.id" :value="dep.id">{{ dep.name }}</option>
            </select>
            <select v-model="moveStockForm.target_department" required>
              <option value="">Куда</option>
              <option v-for="dep in departments" :key="dep.id" :value="dep.id">{{ dep.name }}</option>
            </select>
            <select v-model="moveStockForm.product" required>
              <option value="">Товар</option>
              <option v-for="product in products" :key="product.id" :value="product.id">{{ product.name }}</option>
            </select>
            <input v-model.trim="moveStockForm.grade" placeholder="Сорт" required />
            <input v-model.number="moveStockForm.quantity" type="number" min="1" required />
            <button :disabled="!isAdmin">Переместить</button>
          </form>
        </article>

        <article class="panel">
          <h2>Изменить розничную цену</h2>
          <form class="stack" @submit.prevent="changeRetailPrice">
            <select v-model="priceForm.department_stock_id" required>
              <option value="">Выбери позицию отдела</option>
              <option
                v-for="stock in departmentStocks"
                :key="stock.id"
                :value="stock.id"
              >
                #{{ stock.id }} {{ stock.department_name }} - {{ stock.product_name }} ({{ stock.grade }})
              </option>
            </select>
            <input v-model.number="priceForm.retail_price" type="number" min="0.01" step="0.01" required />
            <button :disabled="!isAdmin">Обновить цену</button>
          </form>
        </article>
      </section>

      <section v-if="activeTab === 'operations'" class="grid-2">
        <article class="panel">
          <h2>Закупка (заявка)</h2>
          <form class="stack" @submit.prevent="createPurchaseOrder">
            <select v-model="purchaseForm.store" required>
              <option value="">Магазин</option>
              <option v-for="store in stores" :key="store.id" :value="store.id">{{ store.name }}</option>
            </select>
            <select v-model="purchaseForm.supplier_base" required>
              <option value="">База</option>
              <option v-for="base in supplierBases" :key="base.id" :value="base.id">{{ base.name }}</option>
            </select>
            <select v-model="purchaseForm.department" required>
              <option value="">Отдел назначения</option>
              <option v-for="dep in departments" :key="dep.id" :value="dep.id">{{ dep.name }}</option>
            </select>
            <textarea v-model="purchaseForm.notes" placeholder="Комментарий"></textarea>

            <div v-for="(item, index) in purchaseForm.items" :key="index" class="item-card">
              <select v-model="item.product" required>
                <option value="">Товар</option>
                <option v-for="product in products" :key="product.id" :value="product.id">{{ product.name }}</option>
              </select>
              <input v-model.trim="item.grade" placeholder="Сорт" required />
              <input v-model.number="item.quantity" type="number" min="1" required />
              <input v-model.number="item.purchase_price" type="number" min="0.01" step="0.01" required />
              <button type="button" @click="removePurchaseItem(index)" :disabled="purchaseForm.items.length <= 1">Удалить</button>
            </div>

            <button type="button" @click="addPurchaseItem">Добавить позицию</button>
            <button :disabled="!isAdmin">Создать заявку</button>
          </form>

          <h3>Список закупок</h3>
          <ul>
            <li v-for="order in purchaseOrders" :key="order.id">
              #{{ order.id }} | {{ order.supplier_base_name }} | {{ order.status }}
              <button v-if="isAdmin && order.status !== 'RECEIVED'" @click="receivePurchase(order.id)">Оприходовать</button>
              <button @click="downloadPurchaseDocument(order.id)">PDF</button>
            </li>
          </ul>
        </article>

        <article class="panel">
          <h2>Продажа</h2>
          <form class="stack" @submit.prevent="createSale">
            <select v-model="saleForm.store" required>
              <option value="">Магазин</option>
              <option v-for="store in stores" :key="store.id" :value="store.id">{{ store.name }}</option>
            </select>
            <select v-model="saleForm.department" required>
              <option value="">Отдел</option>
              <option v-for="dep in departments" :key="dep.id" :value="dep.id">{{ dep.name }}</option>
            </select>
            <textarea v-model="saleForm.notes" placeholder="Комментарий"></textarea>

            <div v-for="(item, index) in saleForm.items" :key="index" class="item-card">
              <select v-model="item.product" required>
                <option value="">Товар</option>
                <option v-for="product in products" :key="product.id" :value="product.id">{{ product.name }}</option>
              </select>
              <input v-model.trim="item.grade" placeholder="Сорт" required />
              <input v-model.number="item.quantity" type="number" min="1" required />
              <input v-model.number="item.retail_price" type="number" min="0.01" step="0.01" required />
              <button type="button" @click="removeSaleItem(index)" :disabled="saleForm.items.length <= 1">Удалить</button>
            </div>

            <button type="button" @click="addSaleItem">Добавить позицию</button>
            <button>Провести продажу</button>
          </form>

          <h3>Список продаж</h3>
          <ul>
            <li v-for="sale in sales" :key="sale.id">
              #{{ sale.id }} | {{ sale.department_name }} | {{ new Date(sale.sold_at).toLocaleString() }}
            </li>
          </ul>
        </article>
      </section>

      <section v-if="activeTab === 'report'" class="panel">
        <h2>Ежемесячный отчет по прибыли</h2>
        <div class="inline-form">
          <label>
            Год
            <input v-model.number="reportForm.year" type="number" min="2000" max="2100" />
          </label>
          <label>
            Месяц
            <input v-model.number="reportForm.month" type="number" min="1" max="12" />
          </label>
          <button @click="loadMonthlyReport">Сформировать</button>
        </div>

        <div v-if="monthlyReport">
          <p>
            Итого закупки: {{ monthlyReport.totals.purchase_total }} руб. |
            Продажи: {{ monthlyReport.totals.sales_total }} руб. |
            Прибыль: {{ monthlyReport.totals.profit }} руб.
          </p>

          <div v-for="dep in monthlyReport.departments" :key="dep.department_id" class="report-card">
            <h3>{{ dep.department_name }}</h3>
            <p>Прибыль отдела: {{ dep.profit }} руб.</p>
            <p>Закуплено: {{ dep.purchased.length }} позиций, Продано: {{ dep.sold.length }} позиций</p>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
:root {
  color-scheme: light;
}

.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
}

.hero {
  background: linear-gradient(135deg, #fff8f0, #f4f1ff);
  border: 1px solid #e4dfd1;
  border-radius: 14px;
  padding: 1rem;
}

.hero h1 {
  margin: 0;
  font-size: 1.8rem;
}

.panel {
  background: #fff;
  border: 1px solid #dadce5;
  border-radius: 12px;
  padding: 1rem;
  margin-top: 1rem;
}

.main-layout {
  margin-top: 1rem;
}

.filter-row {
  display: flex;
  justify-content: flex-start;
}

.login-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.75rem;
  align-items: end;
}

.grid-2 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1rem;
}

.wide {
  grid-column: 1 / -1;
}

.tabs {
  margin-top: 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.tabs button {
  border: 1px solid #9ea7b8;
  background: #f6f8ff;
  border-radius: 999px;
  padding: 0.45rem 0.9rem;
}

.tabs .active {
  background: #1f4fbf;
  color: #fff;
  border-color: #1f4fbf;
}

.stack {
  display: grid;
  gap: 0.5rem;
}

.inline-form {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: end;
}

.item-card {
  border: 1px dashed #c1c5d0;
  border-radius: 10px;
  padding: 0.6rem;
  display: grid;
  gap: 0.4rem;
}

input,
select,
textarea,
button {
  font: inherit;
  padding: 0.5rem;
  border-radius: 8px;
  border: 1px solid #c3cad9;
}

button {
  cursor: pointer;
  background: #eef3ff;
}

button:hover {
  background: #dce7ff;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.user-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ok-msg {
  color: #0f7a34;
}

.error-msg {
  color: #bb2330;
}

.report-card {
  margin-top: 0.8rem;
  padding: 0.8rem;
  border: 1px solid #d5d9e1;
  border-radius: 10px;
}

@media (max-width: 768px) {
  .page {
    padding: 0.6rem;
  }

  .hero h1 {
    font-size: 1.45rem;
  }
}
</style>

