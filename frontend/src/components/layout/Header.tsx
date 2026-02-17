import { useParams } from 'react-router-dom';
import { useChatHistory } from '@/hooks/useChatHistory';

export const Header = () => {
  const { data: history = [] } = useChatHistory();
  const { sessionId } = useParams();

  const currentChat = history.find(item => item.id === sessionId);
  const title = currentChat?.title || (sessionId ? "Untitled Chat" : "New Chat");

  return (
    <header className="h-12 backdrop-blur supports-backdrop-filter:bg-background/60 flex flex-col items-center px-4 sticky top-0 z-10">
      <div className="flex items-center p-4 overflow-hidden">
        <h1 className="font-semibold text-sm truncate max-w-50 md:max-w-md">
          {title}
        </h1>
      </div>
    </header>
  );
};

