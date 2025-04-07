// used by admin dashboard

document.addEventListener('DOMContentLoaded', function () {
    // Mini status chart
    const miniCtx = document.getElementById('miniStatusChart').getContext('2d');
    new Chart(miniCtx, {
        type: 'doughnut',
        data: {
            labels: ['Pending', 'Approved', 'Rejected'],
            datasets: [{
                data: [{{ pending_requisitions }},
            {{ Requisition.query.filter_by(status = 'Approved').count() }}, 
                    {{ Requisition.query.filter_by(status = 'Rejected').count() }}],
    backgroundColor: [
    '#FFCE56',
    '#4BC0C0',
    '#FF6384'
]
        }]
    },
    options: {
    responsive: true,
    cutout: '70%',
    plugins: {
        legend: {
            display: false
        }
    }
}
});
});