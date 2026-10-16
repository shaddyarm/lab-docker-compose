const form = document.querySelector("#valuation-form");
const resultElement = document.querySelector("#result");
const messageElement = document.querySelector("#message");
const historyElement = document.querySelector("#history");
const modelSelect = document.querySelector("#model");
const yearInput = document.querySelector("#year");
const money = new Intl.NumberFormat("ru-RU");

yearInput.max = String(new Date().getFullYear());
yearInput.value = String(new Date().getFullYear() - 5);

async function requestJson(path, options) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Ошибка запроса к серверу.");
  return data;
}

function showStatus(element, text, isError = false) {
  element.textContent = text;
  element.classList.toggle("error", isError);
}

async function loadModels() {
  try {
    const models = await requestJson("/api/models");
    modelSelect.replaceChildren();
    for (const model of models) {
      const option = document.createElement("option");
      option.value = String(model.id);
      option.textContent = model.name;
      modelSelect.append(option);
    }
  } catch (error) {
    showStatus(resultElement, error.message, true);
  }
}

function renderHistory(rows) {
  historyElement.replaceChildren();
  if (rows.length === 0) {
    showStatus(messageElement, "История пока пуста.");
    return;
  }
  showStatus(messageElement, "");
  const table = document.createElement("table");
  const thead = document.createElement("thead");
  const heading = document.createElement("tr");
  for (const label of ["Модель", "Год", "Пробег, км", "Оценка, ₽"]) {
    const cell = document.createElement("th");
    cell.textContent = label;
    heading.append(cell);
  }
  thead.append(heading);
  table.append(thead);
  const tbody = document.createElement("tbody");
  for (const row of rows) {
    const tr = document.createElement("tr");
    for (const value of [row.model_name, row.year, money.format(row.mileage_km), money.format(row.estimated_price_rub)]) {
      const cell = document.createElement("td");
      cell.textContent = String(value);
      tr.append(cell);
    }
    tbody.append(tr);
  }
  table.append(tbody);
  historyElement.append(table);
}

async function loadHistory() {
  showStatus(messageElement, "Загрузка...");
  try {
    renderHistory(await requestJson("/api/valuations"));
  } catch (error) {
    historyElement.replaceChildren();
    showStatus(messageElement, error.message, true);
  }
}

document.querySelector("#show-history").addEventListener("click", loadHistory);
form.addEventListener("submit", async event => {
  event.preventDefault();
  const button = form.querySelector("button[type=submit]");
  button.disabled = true;
  showStatus(resultElement, "Расчёт...");
  const data = new FormData(form);
  try {
    const valuation = await requestJson("/api/valuations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model_id: Number(data.get("model_id")),
        year: Number(data.get("year")),
        mileage_km: Number(data.get("mileage_km")),
      }),
    });
    showStatus(resultElement, `Ориентировочная стоимость: ${money.format(valuation.estimated_price_rub)} ₽`);
    await loadHistory();
  } catch (error) {
    showStatus(resultElement, error.message, true);
  } finally {
    button.disabled = false;
  }
});

loadModels();
