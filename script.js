const BASE = "[http://127.0.0.1](http://127.0.0.1):5001";

// Helper to display JSON nicely
function showResult(elementId, data) {
    document.getElementById(elementId).textContent = JSON.stringify(data, null, 2);
}

// --- One-Click Demo Logic ---
document.getElementById("oneClickDemoBtn").onclick = async function() {
    const resultDiv = document.getElementById("oneClickDemoResult");
    resultDiv.textContent = "Running demo...";

    // Step 1: Generate random property
    const propertyNames = ["Sunny Loft", "Cozy Studio", "Urban Retreat", "Seaside Escape", "Mountain Cabin"];
    const cities = ["Lisbon", "Barcelona", "Berlin", "Paris", "Athens"];
    const countries = ["Portugal", "Spain", "Germany", "France", "Greece"];
    const amenitiesList = [["wifi", "kitchen"], ["wifi", "balcony"], ["kitchen", "washer"], ["wifi", "pool"], ["air conditioning", "wifi"]];
    const bedrooms = [1, 2, 3];
    const randomIdx = () => Math.floor(Math.random() * 5);

    const property = {
        name: propertyNames[randomIdx()],
        original_price: 100 + Math.floor(Math.random() * 100),
        amenities: amenitiesList[randomIdx()],
        bedrooms: bedrooms[Math.floor(Math.random() * bedrooms.length)],
        location: {
            city: cities[randomIdx()],
            country: countries[randomIdx()]
        }
    };

    // Step 2: Generate random user and preferences
    const userId = "user" + Math.floor(Math.random() * 10000);
    const userPrefs = {
        amenities: property.amenities,
        price_max: property.original_price * 0.6,
        bedrooms: property.bedrooms
    };

    // Step 3: Add property
    let resp = await fetch(`${BASE}/properties/add`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(property)
    });
    const addPropResult = await resp.json();

    // Step 4: Register preferences
    resp = await fetch(`${BASE}/users/preferences`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ user_id: userId, preferences: userPrefs })
    });
    const regPrefsResult = await resp.json();

    // Step 5: Find matches
    resp = await fetch(`${BASE}/properties/match/${userId}`);
    const matchesResult = await resp.json();

    // Step 6: Book stay (if matches exist)
    let bookingResult = {};
    let revealResult = {};
    if (matchesResult.matches && matchesResult.matches.length > 0) {
        const propertyId = matchesResult.matches[0].id;
        const today = new Date();
        const checkIn = today.toISOString().slice(0,10);
        const checkOut = new Date(today.getTime() + 4*24*60*60*1000).toISOString().slice(0,10);

        resp = await fetch(`${BASE}/bookings/create`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                user_id: userId,
                property_id: propertyId,
                check_in: checkIn,
                check_out: checkOut
            })
        });
        bookingResult = await resp.json();

        // Step 7: Reveal location
        if (bookingResult.booking_id) {
            resp = await fetch(`${BASE}/bookings/reveal/${bookingResult.booking_id}`);
            revealResult = await resp.json();
        }
    }

    // Step 8: Display results
    resultDiv.innerHTML = `
        <b>Property Added:</b><br><pre>${JSON.stringify(property, null, 2)}</pre>
        <b>User Preferences Registered:</b><br><pre>${JSON.stringify({user_id: userId, preferences: userPrefs}, null, 2)}</pre>
        <b>Matches Found:</b><br><pre>${JSON.stringify(matchesResult.matches, null, 2)}</pre>
        <b>Booking Result:</b><br><pre>${JSON.stringify(bookingResult, null, 2)}</pre>
        <b>Reveal Location:</b><br><pre>${JSON.stringify(revealResult, null, 2)}</pre>
    `;
};

// Scan Airbnb for Mystery Stays
document.getElementById("scanAirbnbForm").onsubmit = async function(e) {
    e.preventDefault();
    const form = e.target;
    const body = {
        city: form.city.value,
        check_in: form.check_in.value,
        check_out: form.check_out.value
    };
    const resp = await fetch(`${BASE}/scan_airbnb`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body)
    });
    const data = await resp.json();
    showResult("scanAirbnbResult", data);
};

// Add Property
document.getElementById("addPropertyForm").onsubmit = async function(e) {
    e.preventDefault();
    const form = e.target;
    const body = {
        name: form.name.value,
        original_price: Number(form.original_price.value),
        amenities: form.amenities.value.split(',').map(a => a.trim()),
        bedrooms: Number(form.bedrooms.value),
        location: {
            city: form.city.value,
            country: form.country.value
        }
    };
    const resp = await fetch(`${BASE}/properties/add`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body)
    });
    showResult("addPropertyResult", await resp.json());
};

// Register Preferences
document.getElementById("registerPreferencesForm").onsubmit = async function(e) {
    e.preventDefault();
    const form = e.target;
    const body = {
        user_id: form.user_id.value,
        preferences: {
            amenities: form.amenities.value.split(',').map(a => a.trim()),
            price_max: Number(form.price_max.value),
            bedrooms: Number(form.bedrooms.value)
        }
    };
    const resp = await fetch(`${BASE}/users/preferences`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body)
    });
    showResult("registerPreferencesResult", await resp.json());
};

// Find Matches
document.getElementById("findMatchesForm").ons