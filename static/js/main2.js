// Initialize the calendar
const calendar = new FullCalendar.Calendar(document.getElementById('calendar'), {
    initialView: 'dayGridMonth',
    dateClick: function(info) {
      // Display the time slots for the selected date
      displayTimeSlots(info.date);
    }
  });
  
  // Display the time slots for the selected date
  function displayTimeSlots(date) {
    // Get the available and occupied time slots for the selected date
    const timeSlots = getTimeSlots(date);
  
    // Display the time slots in the div with the id "timeSlots"
    const timeSlotsDiv = document.getElementById('timeSlots');
    timeSlotsDiv.innerHTML = '';
  
    // Loop through the time slots and display them
    for (const timeSlot of timeSlots) {
      const timeSlotDiv = document.createElement('div');
      timeSlotDiv.textContent = timeSlot.time;
      timeSlotDiv.classList.add('timeSlot');
      if (timeSlot.isAvailable) {
        timeSlotDiv.classList.add('available');
      } else {
        timeSlotDiv.classList.add('occupied');
      }
      timeSlotsDiv.appendChild(timeSlotDiv);
    }
  }
  
  // Get the available and occupied time slots for the selected date
  function getTimeSlots(date) {

    return [
      { time: '9:00', isAvailable: true },
      { time: '10:00', isAvailable: true },
      { time: '11:00', isAvailable: false },
      { time: '12:00', isAvailable: true },
      { time: '13:00', isAvailable: false },
      { time: '14:00', isAvailable: true },
      { time: '15:00', isAvailable: true },
      { time: '16:00', isAvailable: false },
      { time: '17:00', isAvailable: true },
      { time: '18:00', isAvailable: true },
    ];
  }