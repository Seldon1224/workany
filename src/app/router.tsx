import { createBrowserRouter } from 'react-router-dom';
import { HomePage, LibraryPage, TaskDetailPage } from '@/app/pages';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <HomePage />,
  },
  {
    path: '/task/:taskId',
    element: <TaskDetailPage />,
  },
  {
    path: '/library',
    element: <LibraryPage />,
  },
]);
