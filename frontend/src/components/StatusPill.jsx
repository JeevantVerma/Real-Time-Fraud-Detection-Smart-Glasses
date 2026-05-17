const StatusPill = ({ label, className }) => {
  return (
    <span
      className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${className}`}
    >
      {label}
    </span>
  );
};

export default StatusPill;
