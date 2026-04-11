import { type ClassValue, clsx } from "clsx";
import { X } from "lucide-react";
import type React from "react";
import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

interface ModalProps {
	isOpen: boolean;
	onClose: () => void;
	title: string;
	children: React.ReactNode;
	className?: string;
}

export function Modal({
	isOpen,
	onClose,
	title,
	children,
	className,
}: ModalProps) {
	const overlayRef = useRef<HTMLDivElement>(null);

	useEffect(() => {
		const handleEscape = (e: KeyboardEvent) => {
			if (e.key === "Escape") onClose();
		};

		if (isOpen) {
			document.addEventListener("keydown", handleEscape);
			document.body.style.overflow = "hidden";
		}

		return () => {
			document.removeEventListener("keydown", handleEscape);
			document.body.style.overflow = "unset";
		};
	}, [isOpen, onClose]);

	if (!isOpen) return null;

	return createPortal(
		// biome-ignore lint/a11y/useKeyWithClickEvents: standard overlay interaction
		// biome-ignore lint/a11y/noStaticElementInteractions: standard overlay interaction
		<div
			ref={overlayRef}
			className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in"
			onClick={(e) => {
				if (e.target === overlayRef.current) onClose();
			}}
		>
			<div
				className={cn(
					"bg-[#1a1c23] border border-white/10 rounded-2xl shadow-xl w-full max-w-md overflow-hidden flex flex-col",
					className,
				)}
			>
				<div className="flex items-center justify-between p-4 border-b border-white/10">
					<h3 className="font-semibold text-lg">{title}</h3>
					<button
						type="button"
						onClick={onClose}
						className="p-1 rounded-full hover:bg-white/10 transition-colors"
						aria-label="Close modal"
					>
						<X className="w-5 h-5 text-muted-foreground hover:text-white" />
					</button>
				</div>
				<div className="p-4 overflow-y-auto">{children}</div>
			</div>
		</div>,
		document.body,
	);
}
