const form = document.querySelector("#plannerForm");
const statusText = document.querySelector("#statusText");
const currentWeek = document.querySelector("#currentWeek");
const confidence = document.querySelector("#confidence");
const productCount = document.querySelector("#productCount");
const currentFocus = document.querySelector("#currentFocus");
const uncertaintyNote = document.querySelector("#uncertaintyNote");
const calendarAdvice = document.querySelector("#calendarAdvice");
const calendarStatus = document.querySelector("#calendarStatus");
const connectCalendarButton = document.querySelector("#connectCalendarButton");
const addCalendarButton = document.querySelector("#addCalendarButton");
const productsGrid = document.querySelector("#productsGrid");
const timelineGrid = document.querySelector("#timelineGrid");
const fullTimelineGrid = document.querySelector("#fullTimelineGrid");
const fullTimelineSection = document.querySelector("#fullTimelineSection");
let latestCalendarEvents = [];
let calendarConnected = false;

function setStatus(message, isError = false) {
  statusText.textContent = message;
  statusText.style.color = isError ? "#b42348" : "#68777d";
}

function showCalendarCallbackMessage() {
  const params = new URLSearchParams(window.location.search);
  const error = params.get("calendar_error");
  if (error) {
    calendarStatus.textContent = `Google Calendar connection failed: ${error}`;
    calendarStatus.style.color = "#b42348";
    return;
  }
  if (params.get("calendar") === "connected") {
    calendarStatus.textContent = "Google Calendar connected. You can add milestone reminders.";
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderProducts(products) {
  if (!products.length) {
    productsGrid.innerHTML =
      '<div class="empty-state">No product recommendations for this stage.</div>';
    return;
  }

  productsGrid.innerHTML = products
    .map((product) => {
      const reason = product.reason?.en || product.reason?.ar || "";
      const url = product.url || "#";
      return `
        <article class="product-card">
          <div>
            <span class="timing-badge">${escapeHtml(product.timing)}</span>
            <h4>${escapeHtml(product.name)}</h4>
            <p>${escapeHtml(reason)}</p>
          </div>
          <a class="shop-link" href="${escapeHtml(url)}" target="_blank" rel="noreferrer">
            View on Mumzworld
          </a>
        </article>
      `;
    })
    .join("");
}

function renderTimeline(preview, milestones) {
  const items = [
    ...preview.map((item) => ({
      label: `Week ${item.week}`,
      text: `${item.focus}${item.buy?.length ? ` Buy: ${item.buy.join(", ")}` : ""}`,
    })),
    ...milestones.map((item) => ({
      label: `Milestone ${item.week}`,
      text: item.event,
    })),
  ];

  if (!items.length) {
    timelineGrid.innerHTML = '<div class="empty-state">No timeline yet.</div>';
    return;
  }

  timelineGrid.innerHTML = items
    .map(
      (item) => `
        <article class="timeline-item">
          <strong>${escapeHtml(item.label)}</strong>
          <p>${escapeHtml(item.text)}</p>
        </article>
      `,
    )
    .join("");
}

function renderFullTimeline(fullTimeline) {
  if (!fullTimeline || !fullTimeline.length) {
    fullTimelineSection.style.display = "none";
    return;
  }

  fullTimelineSection.style.display = "";
  fullTimelineGrid.innerHTML = fullTimeline
    .map(
      (item) => `
        <article class="timeline-item">
          <strong>${escapeHtml(`Week ${item.week}`)}</strong>
          <p>${escapeHtml(item.focus)}${item.buy?.length ? `<br>Buy: ${escapeHtml(item.buy.join(", "))}` : ""}</p>
        </article>
      `,
    )
    .join("");
}

function renderPlan(data) {
  latestCalendarEvents = data.calendar_events || [];
  currentWeek.textContent = data.current_week ?? "--";
  confidence.textContent =
    typeof data.confidence === "number"
      ? `${Math.round(data.confidence * 100)}%`
      : "--";
  productCount.textContent = data.products?.length ?? 0;
  currentFocus.textContent = data.current_focus || "Plan generated.";
  uncertaintyNote.textContent = data.uncertainty_note || "";
  calendarAdvice.textContent = data.calendar_advice || "No calendar advice returned.";
  addCalendarButton.disabled = !calendarConnected || latestCalendarEvents.length === 0;
  renderProducts(data.products || []);
  renderTimeline(data.next_2_weeks_preview || [], data.milestones || []);
  renderFullTimeline(data.full_timeline || null);
}

async function refreshCalendarStatus() {
  try {
    const response = await fetch("/google-calendar/status");
    const data = await response.json();
    calendarConnected = Boolean(data.connected);

    if (!data.configured) {
      calendarStatus.textContent =
        "Google OAuth is not configured. Add credentials.json to enable calendar sync.";
      connectCalendarButton.disabled = true;
      addCalendarButton.disabled = true;
      return;
    }

    calendarStatus.textContent = calendarConnected
      ? "Google Calendar connected. You can add milestone reminders."
      : "Connect Google Calendar before adding milestone reminders.";
    connectCalendarButton.disabled = calendarConnected;
    addCalendarButton.disabled = !calendarConnected || latestCalendarEvents.length === 0;
  } catch (error) {
    calendarStatus.textContent = "Unable to check Google Calendar connection.";
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const submitButton = form.querySelector("button");
  const dueDate = document.querySelector("#dueDate").value;
  const mode = document.querySelector("#mode").value;

  submitButton.disabled = true;
  setStatus("Creating your plan...");

  try {
    const response = await fetch("/pregnancy-plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ due_date: dueDate, mode }),
    });

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    renderPlan(data);
    setStatus("Plan ready.");
  } catch (error) {
    setStatus(error.message || "Unable to create a plan.", true);
  } finally {
    submitButton.disabled = false;
  }
});

connectCalendarButton.addEventListener("click", async () => {
  calendarStatus.textContent = "Opening Google Calendar consent...";
  try {
    const response = await fetch("/google-calendar/auth");
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Google Calendar is not configured.");
    }
    window.location.href = data.authorization_url;
  } catch (error) {
    calendarStatus.textContent = error.message || "Unable to start Google OAuth.";
  }
});

addCalendarButton.addEventListener("click", async () => {
  if (!latestCalendarEvents.length) {
    calendarStatus.textContent = "Generate a plan before adding calendar milestones.";
    return;
  }

  const approved = window.confirm(
    `This will create ${latestCalendarEvents.length} all-day milestone event(s) in your primary Google Calendar. The event titles, dates, and descriptions will be sent to Google Calendar. Continue?`,
  );
  if (!approved) {
    return;
  }

  addCalendarButton.disabled = true;
  calendarStatus.textContent = "Adding milestone reminders to Google Calendar...";

  try {
    const response = await fetch("/google-calendar/events", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ events: latestCalendarEvents }),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Unable to create Google Calendar events.");
    }
    calendarStatus.textContent = `Added ${data.created.length} milestone reminder(s) to Google Calendar.`;
  } catch (error) {
    calendarStatus.textContent =
      error.message || "Unable to create Google Calendar events.";
  } finally {
    addCalendarButton.disabled = !calendarConnected || latestCalendarEvents.length === 0;
  }
});

refreshCalendarStatus().then(showCalendarCallbackMessage);
