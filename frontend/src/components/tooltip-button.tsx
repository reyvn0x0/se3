import { type LucideIcon } from "lucide-react";
import { Button } from "./ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "./ui/tooltip";

interface TooltipButtonProps {
  icon: LucideIcon;
  label: string;
}

export default function TooltipButton({
  icon: Icon,
  label,
}: TooltipButtonProps) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="outline" size="icon">
          <Icon />
          <span className="sr-only">{label}</span>
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>{label}</p>
      </TooltipContent>
    </Tooltip>
  );
}
