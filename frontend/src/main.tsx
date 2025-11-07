import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/all.css' // 引入全域樣式
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
	<StrictMode>
		<App />
	</StrictMode>,
)
