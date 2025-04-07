
document.addEventListener('DOMContentLoaded', function () {
        // Status Pie Chart
        const statusCtx = document.getElementById('statusChart').getContext('2d');
        const statusChart = new Chart(statusCtx, {
            type: 'pie',
            data: {
                labels: {{ status_labels| safe }},
        datasets: [{
            data: {{ status_counts| safe }},
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
    const dailyChart = new Chart(dailyCtx, {
        type: 'line',
        data: {
            labels: {{ daily_dates| safe }},
    datasets: [{
        label: 'Requisitions',
        data: {{ daily_counts| safe }},
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
    const itemsChart = new Chart(itemsCtx, {
        type: 'bar',
        data: {
            labels: {{ item_names| safe }},
    datasets: [{
        label: 'Total Quantity Requested',
        data: {{ item_quantities| safe }},
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