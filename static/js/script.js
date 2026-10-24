// Mobile navigation
const toggle = document.querySelector(".nav-toggle");
const nav = document.getElementById("nav");
toggle.addEventListener("click", () => {
  toggle.setAttribute("aria-expanded", nav.classList.toggle("open"));
});

// Games page: filter by platform
const filterButtons = document.querySelectorAll(".filters button");
filterButtons.forEach((button) => {
  button.addEventListener("click", () => {
    filterButtons.forEach((b) => b.setAttribute("aria-pressed", b === button));
    document.querySelectorAll(".game[data-platform]").forEach((game) => {
      game.hidden = button.dataset.platform !== "all" && game.dataset.platform !== button.dataset.platform;
    });
  });
});

// Booking form: live total and validation before sending
const bookingForm = document.getElementById("booking-form");
if (bookingForm) {
  const total = document.getElementById("total");
  const error = document.getElementById("form-error");
  const field = (name) => bookingForm.elements[name];

  const updateTotal = () => {
    const price = Number(field("pricing_id").selectedOptions[0].dataset.price);
    const amount = price * Number(field("hours").value) * Number(field("stations").value);
    total.textContent = "₹" + amount.toLocaleString("en-IN");
  };
  ["pricing_id", "hours", "stations"].forEach((name) => field(name).addEventListener("change", updateTotal));
  updateTotal();

  bookingForm.addEventListener("submit", (event) => {
    let message = "";
    const [hour, minute] = (field("start_time").value || "0:0").split(":").map(Number);
    const startMinutes = hour * 60 + minute;
    const endMinutes = startMinutes + Number(field("hours").value) * 60;

    if (!field("name").value.trim()) message = "Enter your name.";
    else if (!/^\d{10}$/.test(field("phone").value.trim())) message = "Enter a 10-digit phone number.";
    else if (!field("play_date").value) message = "Pick a date.";
    else if (!field("start_time").value) message = "Pick a start time.";
    else if (startMinutes < 10 * 60 || endMinutes > 23 * 60) message = "We are open 10:00 to 23:00. Your session must finish by closing time.";

    error.hidden = !message;
    error.textContent = message;
    if (message) event.preventDefault();
  });
}

// Ask before cancelling or removing things in the admin dashboard
document.querySelectorAll("form[data-confirm]").forEach((form) => {
  form.addEventListener("submit", (event) => {
    if (!confirm(form.dataset.confirm)) event.preventDefault();
  });
});
