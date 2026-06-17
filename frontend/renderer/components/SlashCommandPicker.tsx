import { filterSlashCommands } from "../chat/chat-utils";

interface SlashCommandPickerProps {
  input: string;
  selectedIndex: number;
  onSelect: (command: string) => void;
}

export default function SlashCommandPicker({
  input,
  selectedIndex,
  onSelect,
}: SlashCommandPickerProps) {
  const commands = filterSlashCommands(input);
  if (commands.length === 0) {
    return null;
  }

  return (
    <div className="slash-picker" role="listbox" aria-label="Slash commands">
      {commands.map((command, index) => (
        <button
          key={command}
          type="button"
          role="option"
          aria-selected={index === selectedIndex}
          className={`slash-picker-item ${index === selectedIndex ? "slash-picker-item-active" : ""}`}
          onMouseDown={(e) => {
            e.preventDefault();
            onSelect(command);
          }}
        >
          {command}
        </button>
      ))}
    </div>
  );
}
