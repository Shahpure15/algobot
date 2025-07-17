import React from 'react';
import { CustomThemeProvider } from './context/ThemeContext';
import AppRoutes from './AppRoutes';

function App() {
  return (
    <CustomThemeProvider>
      <AppRoutes />
    </CustomThemeProvider>
  );
}

export default App;