function passwordConfirmation() {

    let password = document.getElementById("password").value;
    let confirmPassword = document.getElementById("confirm_password").value;
    let message = document.getElementById("demo");

    if (password.length < 6) {
        message.innerHTML = "Password must be at least 6 characters.";
        message.className = "registrationmessage error";
        return false;
    }

    if (password !== confirmPassword) {
        message.innerHTML = "Passwords do not match.";
        message.className = "registrationmessage error";
        return false;
    }

    message.innerHTML = "Registration data looks good!";
    message.className = "registrationmessage success";

    return true;
}