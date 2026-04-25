import { BrowserRouter, Routes, Route } from 'react-router-dom';
import SurveyPage from './pages/SurveyPage';
import MatchPage from './pages/MatchPage';
import ChatPage from './pages/ChatPage';
import ReportPage from './pages/ReportPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<SurveyPage />} />
        <Route path="/matches/:studentId" element={<MatchPage />} />
        <Route path="/chat/:matchId" element={<ChatPage />} />
        <Route path="/report/:matchId" element={<ReportPage />} />
      </Routes>
    </BrowserRouter>
  );
}
