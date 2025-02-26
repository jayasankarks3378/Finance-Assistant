function closeMessage(closeBtn) {
    let messageDiv = closeBtn.parentElement;
    messageDiv.style.opacity = '0';
    messageDiv.style.transform = 'translateY(-20px)';
    setTimeout(() => messageDiv.style.display = "none", 300);
}

// Auto hide messages after 5 seconds
setTimeout(() => {
    const messages = document.querySelectorAll('.message');
    messages.forEach(msg => {
        msg.style.opacity = '0';
        msg.style.transform = 'translateY(-20px)';
        setTimeout(() => msg.style.display = "none", 300);
    });
}, 5000);