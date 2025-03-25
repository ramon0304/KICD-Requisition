let currentStep = 1;
let items = [];

// Real-time validation
document.getElementById("office_name").addEventListener("blur", () => {
    const officeName = document.getElementById("office_name").value.trim();
    if (!officeName) {
        document.getElementById("office_name").classList.add("is-invalid");
    } else {
        document.getElementById("office_name").classList.remove("is-invalid");
    }
});

document.getElementById("requested_by").addEventListener("blur", () => {
    const requestedBy = document.getElementById("requested_by").value.trim();
    if (!requestedBy) {
        document.getElementById("requested_by").classList.add("is-invalid");
    } else {
        document.getElementById("requested_by").classList.remove("is-invalid");
    }
});

document.getElementById("user_email").addEventListener("blur", () => {
    const email = document.getElementById("user_email").value.trim();
    if (!validateEmail(email)) {
        document.getElementById("user_email").classList.add("is-invalid");
    } else {
        document.getElementById("user_email").classList.remove("is-invalid");
    }
});

// Add items dynamically
function addItem() {
    const itemName = document.getElementById("item_name").value.trim();
    const quantity = document.getElementById("quantity").value.trim();

    if (!itemName) {
        document.getElementById("item_name").classList.add("is-invalid");
        return;
    } else {
        document.getElementById("item_name").classList.remove("is-invalid");
    }

    if (!quantity || isNaN(quantity) || quantity < 1) {
        document.getElementById("quantity").classList.add("is-invalid");
        return;
    } else {
        document.getElementById("quantity").classList.remove("is-invalid");
    }

    items.push({ itemName, quantity });
    document.getElementById("item_name").value = "";
    document.getElementById("quantity").value = "";
    updateItemList();
}

function updateItemList() {
    const itemList = document.getElementById("item_list");
    itemList.innerHTML = items.map((item, index) => `
        <li class="list-group-item">
            <strong>Item ${index + 1}:</strong> ${item.itemName} (Quantity: ${item.quantity})
        </li>
    `).join("");
}

// Form submission
async function submitForm(event) {
    event.preventDefault();
    const modal = new bootstrap.Modal(document.getElementById("confirmationModal"));
    modal.show();

    document.getElementById("confirmSubmitBtn").addEventListener("click", async () => {
        const form = document.getElementById("requisitionForm");
        const submitBtn = document.getElementById("submitBtn");
        
        // Convert form data to JSON
        const formData = {
            office_name: form.office_name.value,
            requested_by: form.requested_by.value,
            user_email: form.user_email.value,
            items: items // Your existing items array
        };

        submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Submitting...`;
        submitBtn.disabled = true;

        try {
            const response = await fetch(form.action, {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            // Handle non-JSON responses (like redirects)
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                if (response.status === 401 || response.status === 403) {
                    throw new Error("Please login to submit the form");
                }
                const text = await response.text();
                throw new Error(`Unexpected response: ${text.substring(0, 100)}`);
            }

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.message || "Submission failed");
            }

            alert(result.message);
            clearForm();
        } catch (error) {
            console.error("Submission error:", error);
            alert(error.message || "An error occurred during submission");
            
            // Redirect to login if unauthorized
            if (error.message.includes("login")) {
                window.location.href = "/login/";
            }
        } finally {
            submitBtn.innerHTML = "Submit";
            submitBtn.disabled = false;
            modal.hide();
        }
    }, { once: true });
}

// Clear form
function clearForm() {
    if (confirm("Are you sure you want to clear the form?")) {
        document.getElementById("requisitionForm").reset();
        items = [];
        updateItemList();
        currentStep = 1;
        document.getElementById("step1").style.display = "block";
        document.getElementById("step2").style.display = "none";
        document.getElementById("step3").style.display = "none";
        document.getElementById("prevBtn").style.display = "none";
        document.getElementById("nextBtn").style.display = "inline-block";
        document.getElementById("submitBtn").style.display = "none";

        // Enable fields in the current step
        const currentStepFields = document.querySelectorAll(`#step${currentStep} input, #step${currentStep} select`);
        currentStepFields.forEach(field => field.disabled = false);

        updateProgressBar();
        updateStepIndicators();
    }
}

// Print form
function printForm() {
    window.print();
}

// Step navigation
function nextStep() {
    let isValid = true;

    // Validate Step 1 fields
    if (currentStep === 1) {
        const officeName = document.getElementById("office_name").value.trim();
        const requestedBy = document.getElementById("requested_by").value.trim();
        const userEmail = document.getElementById("user_email").value.trim();

        if (!officeName) {
            document.getElementById("office_name").classList.add("is-invalid");
            isValid = false;
        } else {
            document.getElementById("office_name").classList.remove("is-invalid");
        }

        if (!requestedBy) {
            document.getElementById("requested_by").classList.add("is-invalid");
            isValid = false;
        } else {
            document.getElementById("requested_by").classList.remove("is-invalid");
        }

        if (!userEmail || !validateEmail(userEmail)) {
            document.getElementById("user_email").classList.add("is-invalid");
            isValid = false;
        } else {
            document.getElementById("user_email").classList.remove("is-invalid");
        }
    }

    // Validate Step 2 fields
    if (currentStep === 2) {
        if (items.length === 0) {
            isValid = false;
            alert("Please add at least one item.");
        }
    }

    if (!isValid) return;

    if (currentStep === 1) {
        document.getElementById("review_office").textContent = document.getElementById("office_name").value;
        document.getElementById("review_name").textContent = document.getElementById("requested_by").value;
        document.getElementById("review_email").textContent = document.getElementById("user_email").value;
    } else if (currentStep === 2) {
        document.getElementById("review_items").innerHTML = items.map((item, index) => `
            <div><strong>Item ${index + 1}:</strong> ${item.itemName} (Quantity: ${item.quantity})</div>
        `).join("");
    }

    if (currentStep < 3) {
        document.getElementById(`step${currentStep}`).style.display = "none";
        currentStep++;
        document.getElementById(`step${currentStep}`).style.display = "block";
        document.getElementById("prevBtn").style.display = "inline-block";
    }

    if (currentStep === 3) {
        document.getElementById("nextBtn").style.display = "none";
        document.getElementById("submitBtn").style.display = "inline-block";
    }

    updateProgressBar();
    updateStepIndicators();
}

function prevStep() {
    if (currentStep > 1) {
        document.getElementById(`step${currentStep}`).style.display = "none";
        currentStep--;
        document.getElementById(`step${currentStep}`).style.display = "block";
        document.getElementById("submitBtn").style.display = "none";
        document.getElementById("nextBtn").style.display = "inline-block";
    }

    if (currentStep === 1) {
        document.getElementById("prevBtn").style.display = "none";
    }

    updateProgressBar();
    updateStepIndicators();
}

function updateProgressBar() {
    const progress = (currentStep / 3) * 100;
    document.getElementById("progressBar").style.width = `${progress}%`;
    document.getElementById("progressBar").setAttribute("aria-valuenow", progress);
}

function updateStepIndicators() {
    document.querySelectorAll(".step-indicator").forEach((step, index) => {
        if (index + 1 === currentStep) {
            step.classList.add("active");
            step.setAttribute("aria-current", "true");
        } else {
            step.classList.remove("active");
            step.removeAttribute("aria-current");
        }
    });
}

function validateEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}