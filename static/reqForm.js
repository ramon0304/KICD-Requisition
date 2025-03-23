let currentStep = 1;
let items = [];

// Real-time validation
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

    if (!itemName || !quantity || isNaN(quantity) || quantity < 1) {
        alert("Please fill in valid item details.");
        return;
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
    event.preventDefault(); // Prevent default form submission

    const form = document.getElementById("requisitionForm"); // ✅ Get the form element directly
    const submitBtn = document.getElementById("submitBtn");
    const formData = new FormData(form); // Capture form data

    console.log("Form data:", Object.fromEntries(formData.entries())); // Log form data for debugging

    submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Submitting...`;
    submitBtn.disabled = true;

    try {
        // Send form data using fetch
        const response = await fetch(form.action, {
            method: form.method || "POST",
            body: formData
        });

        if (response.ok) {
            const result = await response.json(); // Assuming the server returns JSON
            alert(result.message || "Form submitted successfully!");
            form.reset(); // Clear form if submission is successful
        } else {
            alert("Submission failed. Please try again.");
        }
    } catch (error) {
        alert("An error occurred. Please try again.");
        console.error("Error:", error);
    } finally {
        submitBtn.innerHTML = "Submit";
        submitBtn.disabled = false;
    }
}



// Clear form
function clearForm() {
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
    updateProgressBar();
    updateStepIndicators();
}

// Print form
function printForm() {
    window.print();
}

// Step navigation
function nextStep() {
    let isValid = true;

    if (currentStep === 1) {
        const officeName = document.getElementById("office_name").value.trim();
        const requestedBy = document.getElementById("requested_by").value.trim();
        const userEmail = document.getElementById("user_email").value.trim();

        if (!officeName || !requestedBy || !userEmail || !validateEmail(userEmail)) {
            isValid = false;
            document.getElementById("office_name").classList.toggle("is-invalid", !officeName);
            document.getElementById("requested_by").classList.toggle("is-invalid", !requestedBy);
            document.getElementById("user_email").classList.toggle("is-invalid", !userEmail || !validateEmail(userEmail));
        }
    } else if (currentStep === 2) {
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