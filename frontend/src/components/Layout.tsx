import { Outlet } from 'react-router-dom';
import Navbar from './Navbar';

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <footer className="bg-gray-800 text-gray-400 text-center py-4 text-sm">
        <p>Hyderabad Road Reporting Platform &copy; {new Date().getFullYear()}</p>
        <p className="text-xs mt-1">Helping citizens report dangerous roads and hold authorities accountable.</p>
      </footer>
    </div>
  );
}
