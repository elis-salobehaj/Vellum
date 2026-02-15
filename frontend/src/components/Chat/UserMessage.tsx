import { User } from 'lucide-react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

interface UserMessageProps {
  content: string;
  userName?: string;
}

export const UserMessage = ({ content, userName }: UserMessageProps) => {
  const initials = userName
    ? userName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : 'U';

  return (
    <div className="flex gap-4 justify-end group">
      <div className="flex-1 flex justify-end">
        <div className="max-w-[80%] bg-primary text-primary-foreground rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm">
          <p className="text-sm whitespace-pre-wrap break-words">{content}</p>
        </div>
      </div>
      <Avatar className="w-8 h-8 shrink-0">
        <AvatarFallback className="bg-muted text-muted-foreground text-xs">
          {initials}
        </AvatarFallback>
      </Avatar>
    </div>
  );
};
