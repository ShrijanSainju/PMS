// Sample booking data
const bookingData = [
  {
    vehicleId: "CH098834",
    vehicleType: "4 Wheeler",
    slot: "A5",
    checkIn: "03:00pm",
    checkOut: "",
    amount: "Rs.50",
    payment: "",
    status: "",
  },
  {
    vehicleId: "CH098834",
    vehicleType: "4 Wheeler",
    slot: "A5",
    checkIn: "03:00pm",
    checkOut: "05:30pm",
    amount: "Rs.90",
    payment: "Paytm",
    status: "Paid",
  },
  {
    vehicleId: "CH098834",
    vehicleType: "4 Wheeler",
    slot: "A5",
    checkIn: "03:00pm",
    checkOut: "",
    amount: "Rs.70",
    payment: "",
    status: "",
  },
  {
    vehicleId: "CH098834",
    vehicleType: "4 Wheeler",
    slot: "A5",
    checkIn: "03:00pm",
    checkOut: "08:30",
    amount: "Rs.120",
    payment: "Online",
    status: "Paid",
  },
]

// Initialize the dashboard
document.addEventListener("DOMContentLoaded", () => {
  initializeBookingTable()
  initializeChart()
  setupEventListeners()
})

// Populate booking table
function initializeBookingTable() {
  const tableBody = document.getElementById("bookingTableBody")

  bookingData.forEach((booking) => {
    const row = document.createElement("tr")

    row.innerHTML = `
            <td>${booking.vehicleId}<br><small style="color: #9ca3af;">943561789</small></td>
            <td>${booking.vehicleType}</td>
            <td>${booking.slot}</td>
            <td>${booking.checkIn}</td>
            <td>${booking.checkOut}</td>
            <td>${booking.amount}</td>
            <td>${booking.payment}</td>
            <td>${booking.status ? `<span class="status-badge ${booking.status.toLowerCase() === "paid" ? "status-paid" : "status-online"}">${booking.status}</span>` : ""}</td>
        `

    tableBody.appendChild(row)
  })
}

// Initialize chart (simple canvas drawing)
function initializeChart() {
  const canvas = document.getElementById("revenueChart")
  const ctx = canvas.getContext("2d")

  // Set canvas size
  canvas.width = canvas.offsetWidth
  canvas.height = canvas.offsetHeight

  // Sample data points
  const dataPoints = [
    { x: 50, y: 120 },
    { x: 100, y: 80 },
    { x: 150, y: 140 },
    { x: 200, y: 100 },
    { x: 250, y: 160 },
    { x: 300, y: 90 },
  ]

  // Draw chart
  ctx.strokeStyle = "#10b981"
  ctx.lineWidth = 3
  ctx.beginPath()

  dataPoints.forEach((point, index) => {
    if (index === 0) {
      ctx.moveTo(point.x, canvas.height - point.y)
    } else {
      ctx.lineTo(point.x, canvas.height - point.y)
    }
  })

  ctx.stroke()

  // Draw data points
  ctx.fillStyle = "#10b981"
  dataPoints.forEach((point) => {
    ctx.beginPath()
    ctx.arc(point.x, canvas.height - point.y, 4, 0, 2 * Math.PI)
    ctx.fill()
  })

  // Add labels
  ctx.fillStyle = "#6b7280"
  ctx.font = "12px Arial"
  ctx.fillText("3.91 LACS", 120, canvas.height - 140)

  // Y-axis labels
  const yLabels = ["6 L", "5 L", "4 L", "3 L", "2 L"]
  yLabels.forEach((label, index) => {
    ctx.fillText(label, 10, 30 + index * 30)
  })
}

// Setup event listeners
function setupEventListeners() {
  // Toggle buttons
  const checkinBtn = document.getElementById("checkin-btn")
  const checkoutBtn = document.getElementById("checkout-btn")

  checkinBtn.addEventListener("click", () => {
    checkinBtn.classList.add("active")
    checkoutBtn.classList.remove("active")
  })

  checkoutBtn.addEventListener("click", () => {
    checkoutBtn.classList.add("active")
    checkinBtn.classList.remove("active")
  })

  // Time tabs
  const timeTabs = document.querySelectorAll(".time-tab")
  timeTabs.forEach((tab) => {
    tab.addEventListener("click", function () {
      timeTabs.forEach((t) => t.classList.remove("active"))
      this.classList.add("active")
    })
  })

  // Booking tabs
  const bookingTabs = document.querySelectorAll(".booking-tab")
  bookingTabs.forEach((tab) => {
    tab.addEventListener("click", function () {
      bookingTabs.forEach((t) => t.classList.remove("active"))
      this.classList.add("active")
    })
  })

  // Register button
  const registerBtn = document.querySelector(".register-btn")
  registerBtn.addEventListener("click", () => {
    const vehicleNo = document.querySelector('input[placeholder="Vehicle No"]').value
    const phoneNo = document.querySelector('input[placeholder="Phone No"]').value

    if (vehicleNo && phoneNo) {
      alert(`Vehicle ${vehicleNo} registered successfully!`)
      // Clear inputs
      document.querySelector('input[placeholder="Vehicle No"]').value = ""
      document.querySelector('input[placeholder="Phone No"]').value = ""
    } else {
      alert("Please fill in all fields")
    }
  })
}

// Animate progress bars on load
window.addEventListener("load", () => {
  const progressBars = document.querySelectorAll(".progress-fill")
  progressBars.forEach((bar) => {
    const width = bar.style.width
    bar.style.width = "0%"
    setTimeout(() => {
      bar.style.width = width
    }, 500)
  })
})
