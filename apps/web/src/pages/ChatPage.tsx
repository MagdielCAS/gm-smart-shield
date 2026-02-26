import { ChatPanel } from "../components/chat/ChatPanel";

const ChatPage = () => {
	return (
		<div className="space-y-4 h-full flex flex-col">
			<div className="flex items-end justify-between shrink-0">
				<div>
					<h2 className="text-3xl font-bold tracking-tight">AI Chat</h2>
					<p className="mt-2 text-muted-foreground max-w-lg">
						Ask questions about your rules and campaign notes.
					</p>
				</div>
			</div>

			<div className="flex-1 min-h-0">
				<ChatPanel />
			</div>
		</div>
	);
};

export default ChatPage;
