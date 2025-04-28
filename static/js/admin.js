// admin.js
// Récupérer le contexte du canvas
const ctx = document.getElementById('reservationsChart').getContext('2d');

// Créer le graphique
const reservationsChart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: ['Validated', 'Canceled', 'Denied'],
        datasets: [{
            label: 'Number of Reservations',
            data: [
                reservationData.validated,
                reservationData.canceled,
                reservationData.denied
            ],
            backgroundColor: [
                'rgba(75, 192, 192, 0.6)', // Vert clair
                'rgba(255, 99, 132, 0.6)', // Rouge clair
                'rgba(153, 102, 255, 0.6)' // Violet clair
            ],
            borderColor: [
                'rgba(75, 192, 192, 1)',
                'rgba(255, 99, 132, 1)',
                'rgba(153, 102, 255, 1)'
            ],
            borderWidth: 1
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});