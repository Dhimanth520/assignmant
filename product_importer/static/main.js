let currentTaskId = null;
let currentPage = 1;
const pageSize = 50;
let lastLoadedCount = 0;

// CSV Upload
async function uploadCSV() {
    const fileInput = document.getElementById('csvFile');
    if (!fileInput.files.length) return alert("Select a CSV file first");

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    try {
        const res = await fetch("/upload-csv/", { method: "POST", body: formData });
        if (!res.ok) throw new Error("Upload failed");
        const data = await res.json();
        currentTaskId = data.task_id;
        document.getElementById("uploadStatus").innerText = "Processing CSV...";
        pollProgress();
    } catch (err) {
        document.getElementById("uploadStatus").innerText = "Upload failed ";
        alert("CSV upload failed. Please retry.");
    }
}

async function pollProgress() {
    if (!currentTaskId) return;
    const res = await fetch(`/upload-progress/${currentTaskId}`);
    const data = await res.json();
    const progress = data.progress;
    const fill = document.getElementById("progressFill");
    fill.style.width = progress + "%";
    fill.innerText = progress + "%";

    if (progress < 100) {
        setTimeout(pollProgress, 500);
    } else {
        document.getElementById("uploadStatus").innerText = "Import Complete!";
        alert("Import completed successfully!");
        showAllProducts();
    }
}

// Load Products (includes pagination and filter)
async function loadProducts() {
    const sku = document.getElementById("filterSku")?.value || "";
    const name = document.getElementById("filterName")?.value || "";
    const active = document.getElementById("filterActive")?.value || "";

    const skip = (currentPage - 1) * pageSize;
    let url = `/products/?skip=${skip}&limit=${pageSize}`;
    if (sku) url += `&filter_sku=${encodeURIComponent(sku)}`;
    if (name) url += `&filter_name=${encodeURIComponent(name)}`;
    if (active) url += `&filter_active=${encodeURIComponent(active)}`;

    const res = await fetch(url);
    const products = await res.json();
    lastLoadedCount = products.length;

    const tbody = document.querySelector("#productTable tbody");
    tbody.innerHTML = "";

    if (!products.length && currentPage > 1) {
        currentPage--;
        return loadProducts();
    }

    products.forEach(p => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${p.id}</td>
            <td>${p.sku}</td>
            <td>${p.name}</td>
            <td>${p.description || ""}</td>
            <td>${p.active ? "Success" : "Error"}</td>
            <td>
                <button onclick="editProduct(${p.id}, '${p.sku}', '${p.name}', '${p.description}', ${p.active})">Edit</button>
                <button onclick="deleteProduct(${p.id})">Delete</button>
            </td>
        `;
        tbody.appendChild(row);
    });

    document.getElementById("pageInfo").innerText = `Page ${currentPage}`;
    updatePaginationButtons();
}

// Pagination
function changePage(direction) {
    if (direction === -1 && currentPage > 1) {
        currentPage--;
        loadProducts();
    } else if (direction === 1 && lastLoadedCount === pageSize) {
        currentPage++;
        loadProducts();
    }
}

function updatePaginationButtons() {
    const prevBtn = document.getElementById("prevPage");
    const nextBtn = document.getElementById("nextPage");
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = lastLoadedCount < pageSize;
}

// Reset filters and show all products
function showAllProducts() {
    document.getElementById("filterSku").value = "";
    document.getElementById("filterName").value = "";
    document.getElementById("filterActive").value = "";
    currentPage = 1;
    loadProducts();
}

// Create / Update Product
function editProduct(id, sku, name, description, active) {
    document.getElementById("productId").value = id;
    document.getElementById("sku").value = sku;
    document.getElementById("name").value = name;
    document.getElementById("description").value = description;
    document.getElementById("active").value = active;
}

async function saveProduct() {
    const id = document.getElementById("productId").value;
    const sku = document.getElementById("sku").value;
    const name = document.getElementById("name").value;
    const description = document.getElementById("description").value;
    const active = document.getElementById("active").value === "true";

    if (!sku || !name) return alert("SKU and Name are required!");

    const body = { sku, name, description, active };
    let res;

    if (id) {
        res = await fetch(`/products/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
    } else {
        res = await fetch(`/products/`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
    }

    if (res.ok) {
        alert(id ? "Product updated successfully!" : "Product created successfully!");
        document.getElementById("productId").value = "";
        showAllProducts();
    } else {
        const error = await res.json();
        alert("Error " + (error.detail || "Error saving product"));
    }
}

// Delete Product
async function deleteProduct(id) {
    if (!confirm("Are you sure you want to delete this product?")) return;
    const res = await fetch(`/products/${id}`, { method: "DELETE" });
    if (res.ok) showAllProducts();
    else alert("Failed to delete product");
}

// Bulk Delete
async function deleteAllProducts() {
    if (!confirm("Are you sure? This will delete ALL products!")) return;
    const res = await fetch(`/products/`, { method: "DELETE" });
    if (res.ok) {
        currentPage = 1;
        showAllProducts();
    } else alert("Failed to delete all products");
}

// WEBHOOK MANAGEMENT
let editingWebhookId = null;

async function loadWebhooks() {
    const res = await fetch("/webhooks/");
    const webhooks = await res.json();

    const tbody = document.querySelector("#webhookTable tbody");
    tbody.innerHTML = "";

    webhooks.forEach(w => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${w.id}</td>
            <td>${w.url}</td>
            <td>${w.event}</td>
            <td>${w.enabled ? "Success" : "Error"}</td>
            <td>
                <button onclick="editWebhook(${w.id}, '${w.url}', '${w.event}', ${w.enabled})">Edit</button>
                <button onclick="testWebhook(${w.id})">Test</button>
                <button onclick="deleteWebhook(${w.id})">Delete</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function editWebhook(id, url, event, enabled) {
    editingWebhookId = id;
    document.getElementById("webhookId").value = id;
    document.getElementById("webhookUrl").value = url;
    document.getElementById("webhookEvent").value = event;
    document.getElementById("webhookEnabled").checked = enabled;
}

async function saveWebhook() {
    const url = document.getElementById("webhookUrl").value;
    const event_type = document.getElementById("webhookEvent").value;
    const enabled = document.getElementById("webhookEnabled").checked;

    if (!url) return alert("Webhook URL is required!");

    const body = { url, event: event_type, enabled };
    let res;

    if (editingWebhookId) {
        res = await fetch(`/webhooks/${editingWebhookId}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
    } else {
        res = await fetch("/webhooks/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body)
        });
    }

    if (res.ok) {
        editingWebhookId = null;
        document.getElementById("webhookId").value = "";
        document.getElementById("webhookUrl").value = "";
        document.getElementById("webhookEnabled").checked = true;
        loadWebhooks();
    } else {
        const error = await res.json();
        alert("Error " + (error.detail || "Error saving webhook"));
    }
}

async function deleteWebhook(id) {
    if (!confirm("Delete this webhook?")) return;
    const res = await fetch(`/webhooks/${id}`, { method: "DELETE" });
    if (res.ok) loadWebhooks();
    else alert("Failed to delete webhook");
}

async function testWebhook(id) {
    const res = await fetch(`/webhooks/test/${id}`, { method: "POST" });
    if (res.ok) {
        const data = await res.json();
        alert(`Test successful! Status: ${data.status_code}, Time: ${data.response_time_ms.toFixed(2)} ms`);
    } else {
        const err = await res.json();
        alert("Test failed: " + err.detail);
    }
}

// Initialize
window.onload = function() {
    showAllProducts();
    loadWebhooks();
};
