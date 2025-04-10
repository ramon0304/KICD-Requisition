document.addEventListener('DOMContentLoaded', function() {
    // Helper function to safely parse data
    function safeParse(data, defaultValue = []) {
        try {
            return data ? JSON.parse(data) : defaultValue;
        } catch (e) {
            console.error("Error parsing data:", e);
            return defaultValue;
        }
    }

    // Status Pie Chart
    const statusCtx = document.getElementById('statusChart');
    if (statusCtx) {
        new Chart(statusCtx.getContext('2d'), {
            type: 'pie',
            data: {
                labels: safeParse({{ status_labels|tojson|safe }}),
                datasets: [{
                    data: safeParse({{ status_counts|tojson|safe }}),
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
    }

    // Daily Line Chart
    const dailyCtx = document.getElementById('dailyChart');
    if (dailyCtx) {
        new Chart(dailyCtx.getContext('2d'), {
            type: 'line',
            data: {
                labels: safeParse({{ daily_dates|tojson|safe }}),
                datasets: [{
                    label: 'Requisitions',
                    data: safeParse({{ daily_counts|tojson|safe }}),
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
    }

    // Items Bar Chart
    const itemsCtx = document.getElementById('itemsChart');
    if (itemsCtx) {
        new Chart(itemsCtx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: safeParse({{ item_names|tojson|safe }}),
                datasets: [{
                    label: 'Total Quantity Requested',
                    data: safeParse({{ item_quantities|tojson|safe }}),
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
    }
});