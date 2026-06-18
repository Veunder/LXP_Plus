<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { api } from "./api";

const laptops = ref([]);
const teachers = ref([]);
const classrooms = ref([]);
const loading = ref(false);
const error = ref("");
const showForm = ref(false);
const activeFilter = ref("all");
const CURRENT_TEACHER_NAME = "Юдин М. Д.";
const toast = reactive({
  visible: false,
  message: "",
  tone: "warning",
});
let toastTimer = null;

const form = reactive({
  teacher_id: "",
  classroom_id: "",
  subject_name: "",
  items: [emptyItem()],
});

function emptyItem() {
  return {
    laptop_id: "",
    student_full_name: "",
    student_group: "",
    missing_keys_count: 0,
    has_mouse: false,
    has_charger: false,
  };
}

const currentTeacher = computed(() => teachers.value.find((teacher) => teacher.full_name === CURRENT_TEACHER_NAME) || null);
const freeLaptops = computed(() => laptops.value.filter((item) => item.status === "free"));
const busyLaptops = computed(() => laptops.value.filter((item) => item.status === "issued"));
const myBookedLaptops = computed(() => laptops.value.filter((item) => item.teacher_id === currentTeacher.value?.id));
const busyCount = computed(() => busyLaptops.value.length);
const myBookingsCount = computed(() => myBookedLaptops.value.length);

const statCards = computed(() => [
  { key: "all", label: "Всего устройств", value: laptops.value.length, valueClass: "" },
  { key: "free", label: "Свободны сейчас", value: freeLaptops.value.length, valueClass: "green" },
  { key: "busy", label: "Заняты сейчас", value: busyCount.value, valueClass: "amber" },
  { key: "mine", label: "Мои бронирования", value: myBookingsCount.value, valueClass: "violet" },
]);

const filteredLaptops = computed(() => {
  if (activeFilter.value === "free") return freeLaptops.value;
  if (activeFilter.value === "busy") return busyLaptops.value;
  if (activeFilter.value === "mine") return myBookedLaptops.value;
  return laptops.value;
});

function showToast(message, tone = "warning") {
  toast.message = message;
  toast.tone = tone;
  toast.visible = true;
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    toast.visible = false;
  }, 3500);
}

function isMyBooking(laptop) {
  return laptop.teacher_id === currentTeacher.value?.id;
}

function setFilter(filterKey) {
  activeFilter.value = filterKey;
}

function selectedLaptopIds(excludedIndex) {
  return new Set(
    form.items
      .filter((_, index) => index !== excludedIndex)
      .map((item) => Number(item.laptop_id))
      .filter(Boolean),
  );
}

function availableLaptopsFor(index) {
  const takenIds = selectedLaptopIds(index);
  return freeLaptops.value.filter((laptop) => !takenIds.has(laptop.id));
}

function normalizeText(value) {
  return String(value || "").trim().toLowerCase().replace(/\s+/g, " ");
}

function studentKey(fullName, group) {
  return `${normalizeText(fullName)}::${normalizeText(group)}`;
}

async function loadData() {
  loading.value = true;
  error.value = "";
  try {
    const [laptopsData, teachersData, classroomsData] = await Promise.all([
      api.getLaptops(),
      api.getTeachers(),
      api.getClassrooms(),
    ]);
    laptops.value = laptopsData;
    teachers.value = teachersData;
    classrooms.value = classroomsData;
    if (!form.teacher_id && currentTeacher.value) {
      form.teacher_id = String(currentTeacher.value.id);
    }
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

function addItem() {
  if (form.items.length < 10) form.items.push(emptyItem());
}

function removeItem(index) {
  form.items.splice(index, 1);
}

function openIssueForm() {
  if (currentTeacher.value) {
    form.teacher_id = String(currentTeacher.value.id);
  }
  showForm.value = true;
}

async function releaseLaptop(laptop) {
  try {
    await api.releaseLaptop(laptop.id);
    await loadData();
    showToast(`Ноутбук NB-${String(laptop.number).padStart(3, "0")} освобожден.`, "success");
  } catch (err) {
    showToast(err.message || "Не удалось освободить ноутбук.");
  }
}

async function submitIssue() {
  error.value = "";
  try {
    const laptopIds = form.items.map((item) => Number(item.laptop_id)).filter(Boolean);
    if (laptopIds.length !== new Set(laptopIds).size) {
      showToast("Один и тот же ноутбук нельзя выбрать для двух учеников.");
      return;
    }

    const requestStudentKeys = form.items
      .map((item) => studentKey(item.student_full_name, item.student_group))
      .filter((key) => key !== "::");
    if (requestStudentKeys.length !== new Set(requestStudentKeys).size) {
      showToast("Ученик из одной и той же группы не может получить два ноутбука.");
      return;
    }

    const activeStudentKeys = new Set(
      laptops.value
        .filter((item) => item.status === "issued")
        .map((item) => studentKey(item.student_full_name, item.student_group)),
    );
    if (requestStudentKeys.some((key) => activeStudentKeys.has(key))) {
      showToast("На этого ученика из этой группы ноутбук уже взят.");
      return;
    }

    await api.createIssue({
      teacher_id: Number(form.teacher_id),
      classroom_id: Number(form.classroom_id),
      subject_name: form.subject_name,
      items: form.items.map((item) => ({
        ...item,
        laptop_id: Number(item.laptop_id),
        missing_keys_count: Number(item.missing_keys_count || 0),
      })),
    });

    showForm.value = false;
    form.teacher_id = currentTeacher.value ? String(currentTeacher.value.id) : "";
    form.classroom_id = "";
    form.subject_name = "";
    form.items = [emptyItem()];
    await loadData();
    activeFilter.value = "mine";
    showToast("Выдача ноутбуков сохранена.", "success");
  } catch (err) {
    const message = err.message || "Не удалось сохранить выдачу.";
    if (message.includes("already has a laptop")) {
      showToast("На этого ученика из этой группы ноутбук уже взят.");
      return;
    }
    showToast(message);
  }
}

onMounted(loadData);
</script>

<template>
  <main class="page">
    <header class="topbar">
      <div class="logo" aria-hidden="true"><span></span><span></span><span></span><span></span></div>
      <nav>
        <a>Главная</a>
        <a>Расписание</a>
        <a>Обучение</a>
        <a class="active">Ноутбуки</a>
      </nav>
      <div class="topbar-right">
        <button class="topbar-icon" type="button" aria-label="Информация">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
            <circle cx="12" cy="12" r="9"></circle>
            <path d="M12 10v5"></path>
            <path d="M12 7.5h.01"></path>
          </svg>
        </button>
        <button class="topbar-icon" type="button" aria-label="Уведомления">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
            <path d="M15 17H20L18.6 15.6a1.2 1.2 0 0 1-.6-1V11a6 6 0 1 0-12 0v3.6a1.2 1.2 0 0 1-.6 1L4 17h5"></path>
            <path d="M9 17a3 3 0 0 0 6 0"></path>
          </svg>
        </button>
        <button class="topbar-icon" type="button" aria-label="Реакции">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
            <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.3a2 2 0 0 0 2-1.7l1.4-9a2 2 0 0 0-2-2.3H14z"></path>
          </svg>
        </button>
        <span class="topbar-user">Юдин Максим Денисович</span>
        <div class="topbar-avatar">ЮМ</div>
      </div>
    </header>

    <section class="content">
      <div class="title-row">
        <h1>Ноутбуки</h1>
        <button class="primary" @click="openIssueForm">Взять ноутбуки</button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="loading" class="muted">Загрузка...</p>

      <div class="stats">
        <button
          v-for="card in statCards"
          :key="card.key"
          class="stat-card"
          :class="{ active: activeFilter === card.key }"
          type="button"
          @click="setFilter(card.key)"
        >
          <span>{{ card.label }}</span>
          <strong :class="card.valueClass">{{ card.value }}</strong>
        </button>
      </div>

      <div class="table-card">
        <table>
          <thead>
            <tr>
              <th>№</th>
              <th>Статус</th>
              <th>Студент</th>
              <th>Группа</th>
              <th>Аудитория</th>
              <th>Пара</th>
              <th>Преподаватель</th>
              <th>Клавиши</th>
              <th class="centered">Мышь</th>
              <th class="centered">Зарядка</th>
              <th>Бронирование</th>
              <th class="centered">Очистить</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="laptop in filteredLaptops" :key="laptop.id">
              <td class="mono">NB-{{ String(laptop.number).padStart(3, "0") }}</td>
              <td>
                <span class="badge" :class="laptop.status">
                  {{ laptop.status === "free" ? "Свободен" : "Занят" }}
                </span>
              </td>
              <td>{{ laptop.student_full_name || "-" }}</td>
              <td>{{ laptop.student_group || "-" }}</td>
              <td>{{ laptop.classroom || "-" }}</td>
              <td>{{ laptop.subject_name || "-" }}</td>
              <td>{{ laptop.teacher || "-" }}</td>
              <td>{{ laptop.missing_keys_count }}</td>
              <td class="centered">
                <span v-if="laptop.has_mouse === true" class="accessory yes">✓</span>
                <span v-else-if="laptop.has_mouse === false" class="accessory no">✕</span>
                <span v-else class="accessory empty">-</span>
              </td>
              <td class="centered">
                <span v-if="laptop.has_charger === true" class="accessory yes">✓</span>
                <span v-else-if="laptop.has_charger === false" class="accessory no">✕</span>
                <span v-else class="accessory empty">-</span>
              </td>
              <td>
                <span v-if="isMyBooking(laptop)" class="reservation-note">ваше бронирование</span>
                <span v-else class="reservation-empty">-</span>
              </td>
              <td class="centered">
                <button
                  v-if="laptop.status === 'issued'"
                  class="clear-btn"
                  type="button"
                  @click="releaseLaptop(laptop)"
                  aria-label="Освободить ноутбук"
                >
                  ✕
                </button>
                <span v-else class="reservation-empty">-</span>
              </td>
            </tr>
            <tr v-if="!filteredLaptops.length">
              <td colspan="12" class="empty-state">По выбранному фильтру ноутбуков нет.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-if="showForm" class="overlay" @click.self="showForm = false">
      <form class="modal" @submit.prevent="submitIssue">
        <h2>Выдача ноутбуков</h2>

        <div class="grid">
          <label>Преподаватель
            <select v-model="form.teacher_id" required>
              <option value="">Выбрать...</option>
              <option v-for="teacher in teachers" :key="teacher.id" :value="teacher.id">{{ teacher.full_name }}</option>
            </select>
          </label>
          <label>Аудитория
            <select v-model="form.classroom_id" required>
              <option value="">Выбрать...</option>
              <option v-for="room in classrooms" :key="room.id" :value="room.id">{{ room.name }}</option>
            </select>
          </label>
          <label class="wide">Название пары
            <input v-model="form.subject_name" required placeholder="Базы данных" />
          </label>
        </div>

        <div class="items">
          <section v-for="(item, index) in form.items" :key="index" class="item-row">
            <select v-model="item.laptop_id" required>
              <option value="">Ноутбук...</option>
              <option v-for="laptop in availableLaptopsFor(index)" :key="laptop.id" :value="laptop.id">
                NB-{{ String(laptop.number).padStart(3, "0") }}
              </option>
            </select>
            <input v-model="item.student_full_name" required placeholder="ФИО ученика" />
            <input v-model="item.student_group" required placeholder="Группа" />
            <input v-model="item.missing_keys_count" type="number" min="0" max="100" />
            <label class="check"><input v-model="item.has_mouse" type="checkbox" /> Мышь</label>
            <label class="check"><input v-model="item.has_charger" type="checkbox" /> Зарядка</label>
            <button v-if="form.items.length > 1" type="button" class="ghost" @click="removeItem(index)">Убрать</button>
          </section>
        </div>

        <div class="footer">
          <button type="button" class="ghost" @click="addItem" :disabled="form.items.length >= 10">Добавить ноутбук</button>
          <button type="button" class="ghost" @click="showForm = false">Отмена</button>
          <button class="primary">Подтвердить</button>
        </div>
      </form>
    </div>

    <transition name="toast-fade">
      <div v-if="toast.visible" class="toast" :class="toast.tone">
        {{ toast.message }}
      </div>
    </transition>
  </main>
</template>
