// static/main.js
let data = {{ data|tojson|safe }};
let labels = {{ labels|tojson|safe }};
let selectedLabel = 0;
let pointSize = 5;
let pointOpacity = 1;

function updatePlot() {
    const traces = [];
    
    // Add background image if exists
    if (window.backgroundImage) {
        traces.push({
            type: 'image',
            source: window.backgroundImage,
            x: parseFloat($('#image-x').val()),
            y: parseFloat($('#image-y').val()),
            sizing: 'stretch',
            opacity: parseFloat($('#image-opacity').val()),
            layer: 'below'
        });
    }

    // Add scatter plot
    const colors = data.map(point => labels[point.label].color);
    traces.push({
        type: 'scatter',
        x: data.map(p => p.x),
        y: data.map(p => p.y),
        mode: 'markers',
        marker: {
            size: pointSize,
            color: colors,
            opacity: pointOpacity
        },
        text: data.map(p => `${labels[p.label].name} (${p.label})`),
        hovertemplate: 'Label: %{text}<br>X: %{x}<br>Y: %{y}<extra></extra>'
    });

    Plotly.newPlot('scatter-plot', traces, {
        dragmode: 'lasso',
        yaxis: { scaleanchor: 'x', scaleratio: 1.6 },
        xaxis_title: 'X',
        yaxis_title: 'Y'
    });
}

function updateLabelControls() {
    const controls = Object.entries(labels).map(([id, info]) => `
        <div class="form-check">
            <input class="form-check-input" type="radio" name="label-select" 
                   value="${id}" ${id == selectedLabel ? 'checked' : ''}>
            <label class="form-check-label">
                ${info.name} (${id})
            </label>
        </div>
    `).join('');
    $('#label-controls').html(controls);
}

// Event handlers
$('#add-label-btn').click(() => {
    const name = $('#new-label-name').val();
    const color = $('#new-label-color').val();
    if (name && color) {
        $.post('/api/add_label', {
            name: name,
            color: color
        }, response => {
            labels[response.id] = { name: name, color: color };
            updateLabelControls();
            updatePlot();
        });
    }
});

$('#scatter-plot').on('plotly_selected', evt => {
    if (evt && evt.points) {
        const points = evt.points.map(p => ({ x: p.x, y: p.y }));
        $.post('/api/update_labels', {
            points: points,
            label: selectedLabel
        }, () => {
            points.forEach(p => {
                const point = data.find(d => d.x === p.x && d.y === p.y);
                if (point) point.label = selectedLabel;
            });
            updatePlot();
        });
    }
});

$('#point-size').on('input', e => {
    pointSize = parseFloat(e.target.value);
    updatePlot();
});

$('#point-opacity').on('input', e => {
    pointOpacity = parseFloat(e.target.value);
    updatePlot();
});

$('#background-image').change(e => {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = evt => {
            window.backgroundImage = evt.target.result;
            updatePlot();
        };
        reader.readAsDataURL(file);
    }
});

$('#download-btn').click(() => {
    window.location.href = '/api/download_labels';
});

// Initialize
updateLabelControls();
updatePlot();