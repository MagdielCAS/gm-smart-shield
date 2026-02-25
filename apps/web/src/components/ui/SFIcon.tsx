import type { LucideIcon, LucideProps } from "lucide-react";
import { cn } from "@/lib/utils";

interface SFIconProps extends LucideProps {
	icon: LucideIcon;
}

export const SFIcon = ({
	icon: Icon,
	className,
	strokeWidth = 1.5,
	...props
}: SFIconProps) => {
	return (
		<Icon
			className={cn("sf-symbol", className)}
			strokeWidth={strokeWidth}
			{...props}
		/>
	);
};
