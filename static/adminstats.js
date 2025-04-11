document.addEventListener('DOMContentLoaded', function() {
    // Verify data exists
    if (typeof chartData === 'undefined') {
        console.error('chartData is not defined!');
        return;
    }
    
    console.log("Chart Data:", chartData); 

    // 1. Status Chart (Pie)
    try {
        new Chart(
            document.getElementById('statusChart').getContext('2d'),
            {
                type: 'pie',
                data: {
                    labels: chartData.status.labels,
                    datasets: [{
                        data: chartData.status.counts,
                        backgroundColor: ['#4CAF50', '#FFC107', '#F44336']
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: { display: true, text: 'Requisitions by Status' }
                    }
                }
            }
        );
    } catch (error) {
        console.error("Status chart error:", error);
    }

    // 2. Daily Chart (Line)
    try {
        new Chart(
            document.getElementById('dailyChart').getContext('2d'),
            {
                type: 'line',
                data: {
                    labels: chartData.daily.dates,
                    datasets: [{
                        label: 'Daily Requisitions',
                        data: chartData.daily.counts,
                        borderColor: '#3A84FF',
                        backgroundColor: 'rgba(58, 132, 255, 0.1)',
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        title: { display: true, text: 'Daily Requisitions' }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            }
        );
    } catch (error) {
        console.error("Daily chart error:", error);
    }

    // 3. Items Chart (Bar)
    try {
        new Chart(
            document.getElementById('itemsChart').getContext('2d'),
            {
                type: 'bar',
                data: {
                    labels: chartData.items.names,
                    datasets: [{
                        label: 'Quantity Requested',
                        data: chartData.items.quantities,
                        backgroundColor: '#FF6384'
                    }]
                },
                options: {
                    responsive: true,
                    indexAxis: 'y',  // Horizontal bars
                    plugins: {
                        title: { display: true, text: 'Top Requested Items' }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            }
        );
    } catch (error) {
        console.error("Items chart error:", error);
    }
});