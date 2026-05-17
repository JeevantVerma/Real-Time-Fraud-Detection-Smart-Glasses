const ResultCard = ({
  title,
  value,
  subtitle,
  badgeText,
  badgeClass,
  withPanel = true,
}) => {
  const content = (
    <div className="flex flex-col gap-2">
      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
        {subtitle}
      </p>
      <h3 className="text-lg font-display font-semibold">{value}</h3>
      <div className="flex items-center gap-3">
        <span className="text-3xl font-mono text-white">{title}</span>
        {badgeText && (
          <span className={`rounded-full px-3 py-1 text-xs font-semibold ${badgeClass}`}>
            {badgeText}
          </span>
        )}
      </div>
    </div>
  );

  if (!withPanel) {
    return content;
  }

  return <div className="glass-panel rounded-2xl p-6">{content}</div>;
};

export default ResultCard;
