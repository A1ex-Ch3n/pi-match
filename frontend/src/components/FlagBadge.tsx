interface FlagBadgeProps {
  type: 'direct' | 'indirect' | 'citizenship' | 'funding';
  via?: string;
}

const CONFIG = {
  direct: {
    emoji: '🤝',
    label: 'Direct Connection',
    classes: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  },
  indirect: {
    emoji: '🔗',
    label: 'Indirect Connection',
    classes: 'bg-blue-100 text-blue-800 border-blue-200',
  },
  citizenship: {
    emoji: '🇺🇸',
    label: 'Citizenship Required',
    classes: 'bg-amber-100 text-amber-800 border-amber-200',
  },
  funding: {
    emoji: '💰',
    label: 'Active Funding',
    classes: 'bg-violet-100 text-violet-800 border-violet-200',
  },
};

export default function FlagBadge({ type, via }: FlagBadgeProps) {
  const { emoji, label, classes } = CONFIG[type];
  const text = type === 'indirect' && via ? `${label} via ${via}` : label;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${classes}`}>
      <span>{emoji}</span>
      <span>{text}</span>
    </span>
  );
}
