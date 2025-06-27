import {
  BookMarked,
  CalendarArrowDown,
  CalendarArrowUp,
  Filter,
  Plus,
} from "lucide-react";
import TooltipButton from "./tooltip-button";

export default function AppHeader() {
  return (
    <header className="px-4">
      <div className="container max-w-4xl mx-auto bg-secondary font-medium py-3 px-4 text-foreground rounded-b-xl flex items-center justify-between">
        <h1>Stundenplan</h1>
        <div className="flex gap-2">
          <TooltipButton icon={Filter} label="Filter hinzufügen" />
          <TooltipButton icon={BookMarked} label="Legende anzeigen" />
          <TooltipButton icon={CalendarArrowDown} label="Importieren" />
          <TooltipButton icon={CalendarArrowUp} label="Exportieren" />
          <TooltipButton icon={Plus} label="Kurs hinzufügen" />
        </div>
      </div>
    </header>
  );
}
