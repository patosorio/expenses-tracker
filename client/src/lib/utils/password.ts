interface PasswordStrength {
  score: number;
  feedback: string;
}

export function checkPasswordStrength(password: string): PasswordStrength {
  if (!password) {
    return { score: 0, feedback: 'Too weak' };
  }

  let score = 0;
  let feedback = '';

  // Length check
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;

  // Character variety checks
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score++;

  // Feedback based on score
  switch (score) {
    case 0:
      feedback = 'Too weak';
      break;
    case 1:
      feedback = 'Weak';
      break;
    case 2:
      feedback = 'Fair';
      break;
    case 3:
      feedback = 'Good';
      break;
    case 4:
      feedback = 'Strong';
      break;
    case 5:
      feedback = 'Very strong';
      break;
    default:
      feedback = 'Too weak';
  }

  return { score, feedback };
} 