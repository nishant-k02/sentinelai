import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto mt-16 max-w-md text-center">
      <h1 className="text-lg font-semibold text-white">Not found</h1>
      <p className="mt-2 text-sm text-slate-500">
        That page or service doesn&apos;t exist.
      </p>
      <Link
        href="/"
        className="mt-4 inline-block text-sm text-emerald-400 hover:underline"
      >
        Back to overview
      </Link>
    </div>
  );
}
