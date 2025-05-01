{% extends "base.html" %}

{% block content %}
<div class="card shadow-sm">
    <div class="card-header bg-white py-3">
        <div class="row g-3 align-items-center">
            <div class="col-12 col-md-4">
                <h5 class="mb-0 text-primary">
                    Generate Tenant Month Bill
                </h5>
            </div>
        </div>
    </div>
    
    <!-- Django Messages Section -->
    {% if messages %}
    <div class="messages-container px-3 pt-3">
        {% for message in messages %}
        <div class="alert alert-{{ message.tags }} alert-dismissible fade show" role="alert">
            {{ message }}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    <div class="card-body">
        <form id="tenantForm" method="POST" action="{% url 'generate-bill' %}">
            <div class="modal-body">
                {% csrf_token %}
                <div class="row mb-3">
                    <div class="col">
                        <label for="rentalunit" class="form-label fw-bold">RentalUnit</label>
                        <select class="select2-rental" id="unit" name="unit">
                            <option value="" selected>Choose...</option>
                            {% for unit in units %}
                                <option value="{{unit.id}}">{{unit.name}} ({{unit.property}})</option>
                            {% endfor %}
                        </select>
                    </div>
                </div>
                <div class="row mb-3">
                    <div class="col-md-6">
                        <label class="form-label fw-bold">Month</label>
                        <select class="form-select" id="month" name="month">
                            <option value="" selected>Choose...</option>
                            {% for month in months %}
                                <option value="{{month}}">{{month}}</option>
                            {% endfor %}
                        </select>
                    </div>
                    <div class="col-md-6">
                        <label for="year" class="form-label fw-bold">Year</label>
                        <select class="form-select" id="year" name="year">
                            <option value="" selected>Choose...</option>
                            {% for year in years %}
                                <option value="{{year.id}}">{{year.name}}</option>
                            {% endfor %}
                        </select>
                    </div>
                </div>
                <div class="row mb-3">
                    <div class="col">
                        <label for="current_reading" class="form-label fw-bold">Current Reading</label>
                        <input type="number" class="form-control" id="current_reading" name="current_reading" step="0.0001" value="0.0000" required/>
                    </div>
                </div>
            </div>
            <div class="text-center mb-3">
                <button type="submit" class="btn btn-primary">Generate Bill</button>
            </div>
        </form>    
    </div>
</div>
{% endblock content %}

{% block additional_scripts %}
<!-- Make sure the Select2 CSS and JS files are loaded in your base template or add them here -->
<script>
    $(document).ready(function() {
        // Initialize Select2 for rental unit dropdown
        $('.select2-rental').select2({
            theme: 'bootstrap-5',
            width: '100%',
            placeholder: 'Search for a rental unit...',
            allowClear: true
        });
        
        // Auto-hide Django messages after 5 seconds
        setTimeout(function() {
            $('.alert').alert('close');
        }, 5000);
    });
</script>
{% endblock additional_scripts %}

{% block extra_css %}
<!-- If the Select2 CSS is not in your base template, add it here -->
<!-- 
<link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
<link href="https://cdn.jsdelivr.net/npm/select2-bootstrap-5-theme@1.3.0/dist/select2-bootstrap-5-theme.min.css" rel="stylesheet" />
-->
{% endblock extra_css %}
