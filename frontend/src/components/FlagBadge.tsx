interface FlagBadgeProps {
  type: 'direct' | 'indirect' | 'citizenship' | 'funding';
  via?: string;
}

const CONFIG = {
  direct: {
    emoji: '🤝',
    label: 'Direct connection',
    classes: 'bg-forest text-ivory border-forest/0',
  },
  indirect: {
    emoji: '🔗',
    label: 'Indirect connection',
    classes: 'bg-gold-soft text-gold border-gold/20',
  },
  citizenship: {
    emoji: '🇺🇸',
    label: 'Citizenship required',
    classes: 'bg-clay-soft text-clay border-clay/20',
  },
  funding: {
    emoji: '💰',
    label: 'Active funding',
    classes: 'bg-forest-soft text-forest-dark border-forest/15',
  },
};

export default function FlagBadge({ type, via }: FlagBadgeProps) {
  const { emoji, label, classes } = CONFIG[type];
  const text = type === 'indirect' && via ? `${label} via ${via}` : label;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${classes}`}
    >
      <span aria-hidden>{emoji}</span>
      <span>{text}</span>
    </span>
  );
}
