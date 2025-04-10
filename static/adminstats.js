document.addEventListener('DOMContentLoaded', function() {
    // Status Pie Chart
    const statusCtx = document.getElementById('statusChart').getContext('2d');
    new Chart(statusCtx, {
        type: 'pie',
        data: {
            labels: JSON.parse({{ status_labels|tojson|safe }}),
            datasets: [{
                data: JSON.parse({{ status_counts|tojson|safe }}),
                backgroundColor: [
                    '#FFCE56', // Pending - yellow
                    '#4BC0C0', // Approved - teal
                    '#FF6384'  // Rejected - red
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Requisitions by Status'
                }
            }
        }
    });

    // Daily Line Chart
    const dailyCtx = document.getElementById('dailyChart').getContext('2d');
    new Chart(dailyCtx, {
        type: 'line',
        data: {
            labels: JSON.parse({{ daily_dates|tojson|safe }}),
            datasets: [{
                label: 'Requisitions',
                data: JSON.parse({{ daily_counts|tojson|safe }}),
                borderColor: '#36A2EB',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                fill: true,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Daily Requisitions (Last 30 Days)'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });

    // Items Bar Chart
    const itemsCtx = document.getElementById('itemsChart').getContext('2d');
    new Chart(itemsCtx, {
        type: 'bar',
        data: {
            labels: JSON.parse({{ item_names|tojson|safe }}),
            datasets: [{
                label: 'Total Quantity Requested',
                data: JSON.parse({{ item_quantities|tojson|safe }}),
                backgroundColor: '#4BC0C0'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Top Requested Items'
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
});