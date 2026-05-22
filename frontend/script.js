async function generateCard() {
    const username = document.getElementById('username').value;
    if (!username) return alert('Please enter a username');
    
    const container = document.getElementById('card-container');
    container.innerHTML = '<p>Generating...</p>';
    
    try {
        const response = await fetch(`http://localhost:8000/generate/${username}`);
        const data = await response.json();
        container.innerHTML = `<pre>${JSON.stringify(data, null, 2)}</pre>`;
    } catch (error) {
        container.innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
    }
}
