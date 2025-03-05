document.addEventListener("DOMContentLoaded", function() {
    fetch('/api/destinations')
        .then(response => response.json())
        .then(data => {
            let list = document.getElementById("destinations-list");
            data.forEach(destination => {
                let li = document.createElement("li");
                li.textContent = destination.name;
                list.appendChild(li);
            });
        })
        .catch(error => console.error('Error fetching data:', error));
});
