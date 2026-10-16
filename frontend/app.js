const booksElement = document.querySelector("#books");
const messageElement = document.querySelector("#message");
const allButton = document.querySelector("#show-all");
const readButton = document.querySelector("#show-read");
const form = document.querySelector("#book-form");
let currentFilter = "all";

async function requestJson(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Ошибка запроса к серверу.");
  return data;
}

function showMessage(text, isError = false) {
  messageElement.textContent = text;
  messageElement.classList.toggle("error", isError);
}

function renderBooks(books) {
  booksElement.replaceChildren();
  for (const book of books) {
    const card = document.createElement("article");
    card.className = "book-card";
    const title = document.createElement("h3");
    title.textContent = book.title;
    const author = document.createElement("p");
    author.textContent = book.author;
    const badge = document.createElement("span");
    badge.className = `badge${book.is_read ? " read" : ""}`;
    badge.textContent = book.is_read ? "Прочитана" : "В планах";
    card.append(title, author, badge);
    booksElement.append(card);
  }
}

async function loadBooks(filter) {
  currentFilter = filter;
  allButton.classList.toggle("active", filter === "all");
  readButton.classList.toggle("active", filter === "read");
  allButton.setAttribute("aria-pressed", String(filter === "all"));
  readButton.setAttribute("aria-pressed", String(filter === "read"));
  showMessage("Загружаем книги…");
  try {
    const books = await requestJson(`/api/books?status=${filter}`);
    renderBooks(books);
    showMessage(books.length ? "" : "В этой подборке пока нет книг.");
  } catch (error) {
    booksElement.replaceChildren();
    showMessage(error.message, true);
  }
}

async function loadStats() {
  try {
    const stats = await requestJson("/api/stats");
    document.querySelector("#total-count").textContent = stats.total;
    document.querySelector("#read-count").textContent = stats.read;
  } catch {
    document.querySelector("#total-count").textContent = "—";
    document.querySelector("#read-count").textContent = "—";
  }
}

allButton.addEventListener("click", () => loadBooks("all"));
readButton.addEventListener("click", () => loadBooks("read"));
form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submitButton = form.querySelector("button[type=submit]");
  submitButton.disabled = true;
  const data = new FormData(form);
  try {
    await requestJson("/api/books", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: data.get("title"),
        author: data.get("author"),
        is_read: data.get("is_read") === "on",
      }),
    });
    form.reset();
    await Promise.all([loadBooks(currentFilter), loadStats()]);
  } catch (error) {
    showMessage(error.message, true);
  } finally {
    submitButton.disabled = false;
  }
});

loadBooks("all");
loadStats();
