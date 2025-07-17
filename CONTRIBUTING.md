# Contributing to AlgoBot

Thank you for considering contributing to AlgoBot! This document provides guidelines and instructions to help you contribute effectively.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to maintain a positive community.

## How Can I Contribute?

### Reporting Bugs

Before submitting a bug report:

- Check the [issues](https://github.com/yourusername/algobot/issues) to see if the bug has already been reported
- If you're unable to find an open issue addressing the problem, open a new one

When filing a bug report, include:

- A clear and descriptive title
- Detailed steps to reproduce the issue
- Expected behavior vs. actual behavior
- Screenshots if applicable
- Any relevant log output
- Your environment details (OS, browser, etc.)

### Suggesting Features

We welcome feature suggestions! Please provide:

- A clear and descriptive title
- Detailed description of the proposed feature
- Explanation of why this feature would be useful
- Any references or examples

### Pull Requests

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

#### Pull Request Guidelines

- Update the README.md with details of changes if applicable
- Update the documentation if necessary
- The PR should work for all supported Python and Node.js versions
- Follow the code style of the project

## Development Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Install development dependencies
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Code Style

- Backend: Follow PEP 8 style guidelines
- Frontend: Use ESLint and Prettier with provided configuration
- Use meaningful variable and function names
- Comment your code when necessary

## Documentation

We use Google-style docstrings for Python code. For example:

```python
def function_with_types_in_docstring(param1, param2):
    """Example function with types documented in the docstring.
    
    Args:
        param1 (int): The first parameter.
        param2 (str): The second parameter.
        
    Returns:
        bool: The return value. True for success, False otherwise.
    """
    return True
```

For React components, use JSDoc style comments:

```jsx
/**
 * A button component that can be clicked.
 * 
 * @param {Object} props - Component props
 * @param {string} props.label - Button text
 * @param {Function} props.onClick - Click handler function
 * @param {boolean} [props.disabled=false] - Whether button is disabled
 * @returns {React.Element} Button component
 */
function Button({ label, onClick, disabled = false }) {
  // ...
}
```

## License

By contributing to AlgoBot, you agree that your contributions will be licensed under the project's [MIT License](LICENSE).
