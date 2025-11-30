document.addEventListener('DOMContentLoaded', function() {
    const durationInput = document.getElementById('id_expected_duration');
    const feeDisplay = document.getElementById('estimatedFee');
    const selectedSlotInput = document.getElementById('selectedSlotInput') || document.getElementById('id_slot');
    const slotRequiredNotice = document.getElementById('slotRequiredNotice');
    const bookingForm = document.getElementById('bookingForm');
    
    console.log('Form elements:', {
        durationInput,
        selectedSlotInput,
        slotInputId: selectedSlotInput ? selectedSlotInput.id : 'NOT FOUND',
        slotRequiredNotice,
        bookingForm
    });
    
    if (!selectedSlotInput) {
        console.error('CRITICAL: selectedSlotInput not found! Checking all hidden inputs...');
        document.querySelectorAll('input[type="hidden"]').forEach(input => {
            console.log('Found hidden input:', input.id, input.name, input);
        });
    }
    
    function updateFee() {
        if (feeDisplay && durationInput) {
            const duration = parseInt(durationInput.value) || 0;
            const pricePerMinute = 2;
            const fee = duration * pricePerMinute;
            feeDisplay.textContent = '₹' + fee;
        }
    }
    
    if (durationInput) {
        durationInput.addEventListener('input', updateFee);
        updateFee();
    }
    
    function loadParkingSlots() {
        console.log('Starting to fetch slots from /api/slot-status/');
        
        fetch('/api/slot-status/', {
            credentials: 'same-origin',
            headers: {
                'Accept': 'application/json'
            }
        })
            .then(response => {
                console.log('Response received:', response.status, response.statusText);
                if (!response.ok) {
                    throw new Error('HTTP error! status: ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                console.log('Slots data received:', data);
                const grid = document.getElementById('slotGrid');
                grid.innerHTML = '';
                
                if (!Array.isArray(data)) {
                    console.error('Data is not an array:', data);
                    grid.innerHTML = '<div class="text-center text-danger"><p>Invalid data format received</p></div>';
                    return;
                }
                
                if (data.length === 0) {
                    grid.innerHTML = '<div class="text-center text-muted"><p>No parking slots available</p></div>';
                    return;
                }
                
                console.log('Creating slot elements for', data.length, 'slots');
                
                data.forEach(slot => {
                    console.log('Processing slot:', slot);
                    const div = document.createElement('div');
                    div.classList.add('slot-option');
                    
                    const isAvailable = !slot.is_occupied && !slot.is_reserved;
                    
                    if (slot.is_occupied) {
                        div.classList.add('occupied');
                    } else if (slot.is_reserved) {
                        div.classList.add('reserved');
                    }
                    
                    var slotStatus = slot.is_occupied ? 'Occupied' : (slot.is_reserved ? 'Reserved' : 'Available');
                    div.innerHTML = '<div style="font-weight: bold; font-size: 1.1rem;">' + slot.slot_id + '</div>' +
                                    '<small style="font-size: 0.85rem;">' + slotStatus + '</small>';
                    
                    if (isAvailable) {
                        div.addEventListener('click', function() {
                            console.log('Slot clicked:', slot.id, slot.slot_id);
                            document.querySelectorAll('.slot-option').forEach(s => s.classList.remove('selected'));
                            this.classList.add('selected');
                            if (selectedSlotInput) {
                                selectedSlotInput.value = slot.id;
                                console.log('Set selectedSlotInput.value to:', slot.id);
                            } else {
                                console.error('selectedSlotInput is null!');
                            }
                            if (slotRequiredNotice) {
                                slotRequiredNotice.classList.remove('show');
                            }
                        });
                    }
                    
                    grid.appendChild(div);
                });
                
                console.log('Finished creating slot elements');
            })
            .catch(error => {
                console.error('Error fetching slots:', error);
                const grid = document.getElementById('slotGrid');
                grid.innerHTML = '<div class="text-center text-danger"><p>Error: ' + error.message + '</p></div>';
            });
    }
    
    loadParkingSlots();
    
    if (bookingForm) {
        bookingForm.addEventListener('submit', function(e) {
            if (!selectedSlotInput || !selectedSlotInput.value) {
                e.preventDefault();
                if (slotRequiredNotice) {
                    slotRequiredNotice.classList.add('show');
                    slotRequiredNotice.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
                return false;
            }
            
            return confirm('Confirm your parking booking with the selected slot?');
        });
    }
    
    const arrivalInput = document.getElementById('id_scheduled_arrival');
    if (arrivalInput) {
        const now = new Date();
        const minDateTime = now.toISOString().slice(0, 16);
        arrivalInput.setAttribute('min', minDateTime);
        
        const maxDate = new Date();
        maxDate.setDate(maxDate.getDate() + 7);
        const maxDateTime = maxDate.toISOString().slice(0, 16);
        arrivalInput.setAttribute('max', maxDateTime);
    }
});
