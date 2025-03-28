function validateEmail(input) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const alertElement = document.getElementById("email-alert");

  if (!emailRegex.test(input.value)) {
    alertElement.textContent = "* Please enter a valid email address.";
    alertElement.classList.remove("hidden");
    return false;
  } else {
    alertElement.classList.add("hidden");
    return true;
  }
}

function validatePassword(input) {
  const passwordRegex =
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/;
  const alertElement = document.getElementById("password-alert");

  if (!passwordRegex.test(input.value)) {
    alertElement.textContent =
      "* Password must be at least 8 characters long and include uppercase, lowercase, number, and special character.";
    alertElement.classList.remove("hidden");
    return false;
  } else {
    alertElement.classList.add("hidden");
    return true;
  }
}

function validateForm(event) {
  const emailInput = document.getElementById("email");
  const passwordInput = document.getElementById("password");

  let isValid = true;

  if (!validateEmail(emailInput)) {
    isValid = false;
  }

  if (!validatePassword(passwordInput)) {
    isValid = false;
  }

  if (!isValid) {
    event.preventDefault();
  }

  return isValid;
}

document.addEventListener("DOMContentLoaded", () => {
  const emailInput = document.getElementById("email");
  const passwordInput = document.getElementById("password");
  const form = document.getElementById("signupForm");

  emailInput.addEventListener("blur", function () {
    validateEmail(this);
  });

  passwordInput.addEventListener("blur", function () {
    validatePassword(this);
  });

  form.addEventListener("submit", validateForm);
});
