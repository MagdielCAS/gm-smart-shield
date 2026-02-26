import { Bot, Loader2, Send, User } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { streamChat } from "../../lib/api/chat";
import { cn } from "../../lib/utils";
import { GlassButton } from "../ui/GlassButton";
import { GlassCard } from "../ui/GlassCard";
import { SFIcon } from "../ui/SFIcon";

interface Message {
	id: string;
	role: "user" | "assistant";
	content: string;
}

export function ChatPanel() {
	const [messages, setMessages] = useState<Message[]>([
		{
			id: "welcome",
			role: "assistant",
			content:
				"Hello! I'm your GM Assistant. Ask me anything about your campaign or rules.",
		},
	]);
	const [input, setInput] = useState("");
	const [isLoading, setIsLoading] = useState(false);
	const scrollRef = useRef<HTMLDivElement>(null);

	// Auto-scroll to bottom
	useEffect(() => {
		if (scrollRef.current) {
			scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
		}
	}, [messages, isLoading]);

	const handleSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		if (!input.trim() || isLoading) return;

		const userMsg: Message = {
			id: Date.now().toString(),
			role: "user",
			content: input,
		};
		setMessages((prev) => [...prev, userMsg]);
		setInput("");
		setIsLoading(true);

		const botMsgId = (Date.now() + 1).toString();
		setMessages((prev) => [
			...prev,
			{ id: botMsgId, role: "assistant", content: "" },
		]);

		await streamChat({
			query: userMsg.content,
			onChunk: (chunk) => {
				setMessages((prev) =>
					prev.map((m) =>
						m.id === botMsgId ? { ...m, content: m.content + chunk } : m,
					),
				);
			},
			onComplete: () => setIsLoading(false),
			onError: (err) => {
				setMessages((prev) =>
					prev.map((m) =>
						m.id === botMsgId
							? { ...m, content: m.content + `\n\n**Error**: ${err.message}` }
							: m,
					),
				);
				setIsLoading(false);
			},
		});
	};

	return (
		<div className="flex flex-col h-[calc(100vh-12rem)] w-full max-w-4xl mx-auto">
			<div
				ref={scrollRef}
				className="flex-1 overflow-y-auto space-y-6 p-4 scroll-smooth pr-6"
			>
				{messages.map((msg) => (
					<div
						key={msg.id}
						className={cn(
							"flex gap-4 w-full",
							msg.role === "user" ? "flex-row-reverse" : "",
						)}
					>
						<div
							className={cn(
								"h-10 w-10 rounded-full flex items-center justify-center shrink-0 shadow-sm border border-white/10",
								msg.role === "user"
									? "bg-primary text-primary-foreground"
									: "bg-white/10 dark:bg-white/5",
							)}
						>
							<SFIcon
								icon={msg.role === "user" ? User : Bot}
								className="h-5 w-5"
							/>
						</div>

						<GlassCard
							className={cn(
								"p-4 text-sm max-w-[80%] leading-relaxed",
								msg.role === "user"
									? "bg-primary/10 border-primary/20"
									: "bg-white/40 dark:bg-white/5",
							)}
						>
							<div className="markdown-content space-y-2">
								<ReactMarkdown
									remarkPlugins={[remarkGfm]}
									components={{
										ul: ({ node, ...props }) => (
											<ul className="list-disc pl-4 space-y-1" {...props} />
										),
										ol: ({ node, ...props }) => (
											<ol className="list-decimal pl-4 space-y-1" {...props} />
										),
										h1: ({ node, ...props }) => (
											<h1 className="text-xl font-bold mt-2 mb-1" {...props} />
										),
										h2: ({ node, ...props }) => (
											<h2 className="text-lg font-bold mt-2 mb-1" {...props} />
										),
										h3: ({ node, ...props }) => (
											<h3 className="text-md font-bold mt-2 mb-1" {...props} />
										),
										blockquote: ({ node, ...props }) => (
											<blockquote
												className="border-l-4 border-primary/30 pl-4 italic my-2"
												{...props}
											/>
										),
										code: ({ node, inline, className, children, ...props }: any) => {
											return inline ? (
												<code
													className="bg-black/10 dark:bg-white/10 px-1 py-0.5 rounded font-mono text-xs"
													{...props}
												>
													{children}
												</code>
											) : (
												<pre className="bg-black/10 dark:bg-white/5 p-3 rounded-lg overflow-x-auto my-2 border border-white/5">
													<code className="font-mono text-xs block" {...props}>
														{children}
													</code>
												</pre>
											);
										},
									}}
								>
									{msg.content}
								</ReactMarkdown>
							</div>
							{msg.role === "assistant" &&
								isLoading &&
								msg.id === messages[messages.length - 1].id && (
									<span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse align-middle" />
								)}
						</GlassCard>
					</div>
				))}
			</div>

			<div className="p-4 pt-2">
				<form onSubmit={handleSubmit} className="relative flex gap-2 items-end">
					<GlassCard className="flex-1 p-0 overflow-hidden flex items-center bg-white/60 dark:bg-black/20 focus-within:ring-2 ring-primary/50 transition-all">
						<input
							value={input}
							onChange={(e) => setInput(e.target.value)}
							placeholder="Ask a question..."
							className="flex-1 bg-transparent border-none px-4 py-4 focus:outline-none placeholder:text-muted-foreground"
							disabled={isLoading}
						/>
						<div className="pr-2">
							<GlassButton
								type="submit"
								disabled={!input.trim() || isLoading}
								size="md"
								variant="ghost"
								className={cn(
									"h-10 w-10 p-0 rounded-full transition-all",
									input.trim()
										? "text-primary hover:bg-primary/10"
										: "opacity-50",
								)}
							>
								{isLoading ? (
									<Loader2 className="h-5 w-5 animate-spin" />
								) : (
									<Send className="h-5 w-5" />
								)}
							</GlassButton>
						</div>
					</GlassCard>
				</form>
			</div>
		</div>
	);
}
