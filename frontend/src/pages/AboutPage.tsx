import { Link } from 'react-router-dom';

export default function AboutPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">About HydRoads</h1>

      <Section title="What is this platform?">
        <p>
          HydRoads is a community-driven platform for reporting and tracking dangerous road
          conditions in Hyderabad. Citizens can upload photos, pin locations, and help build a
          public accountability map connecting road issues to the authorities responsible for
          fixing them.
        </p>
      </Section>

      <Section title="How to report an issue">
        <ol className="list-decimal list-inside space-y-2">
          <li><strong>Take a photo</strong> — Capture the road issue clearly from your phone.</li>
          <li><strong>Mark the location</strong> — GPS auto-captures your position, or you can drag the pin on the map.</li>
          <li><strong>Select type &amp; severity</strong> — Choose from categories like pothole, waterlogging, open manhole, etc.</li>
          <li><strong>Add details</strong> — Describe the issue, mention landmarks or road names.</li>
          <li><strong>Check for duplicates</strong> — We'll show nearby existing reports so you can confirm them instead.</li>
          <li><strong>Submit</strong> — Your report goes live after a quick moderation review.</li>
        </ol>
      </Section>

      <Section title="How authority resolution works">
        <p>
          When you report a road issue, our system automatically determines which government
          authority is most likely responsible — GHMC, HMDA, R&amp;B, or NHAI — based on the
          location's ward, zone, and road segment data.
        </p>
        <p className="mt-2">
          This uses a multi-step resolution engine that checks special road zones, road
          segment mappings, municipal boundaries, and road class inference. Each lookup
          receives a <strong>confidence score</strong> so you know how reliable it is.
        </p>
      </Section>

      <Section title="What does 'confidence' mean?">
        <div className="space-y-1">
          <p><span className="text-green-600 font-medium">High confidence</span> — Strong match from explicit mapping data.</p>
          <p><span className="text-yellow-600 font-medium">Medium confidence</span> — Good match from boundary containment.</p>
          <p><span className="text-orange-600 font-medium">Low confidence</span> — Inferred from road class or partial data.</p>
          <p><span className="text-red-600 font-medium">Very low</span> — Best guess; may need manual verification.</p>
        </div>
      </Section>

      <Section title="How duplicates are handled">
        <p>
          When you submit a report, we check for existing issues within 30 meters of the same
          type. If a match is found, you can choose to confirm the existing issue instead of
          creating a duplicate. This strengthens the verification score and prevents clutter.
        </p>
      </Section>

      <Section title="How to support / confirm issues">
        <p>
          On any issue page, you can use the confirmation buttons:
        </p>
        <ul className="list-disc list-inside mt-2 space-y-1">
          <li><strong>"I've seen this too"</strong> — Confirms the issue exists, boosts verification.</li>
          <li><strong>"This is dangerous"</strong> — Flags severity, draws attention.</li>
          <li><strong>"Still exists"</strong> — Keeps the issue active, resets age tracking.</li>
          <li><strong>"Fixed"</strong> — Multiple confirmations can trigger resolution review.</li>
        </ul>
      </Section>

      <Section title="Privacy and data handling">
        <p>
          Anonymous reporting is supported. If you register, your email is used only for
          authentication. Location data is used to map issues to wards and authorities.
          Images are stored securely and publicly visible only after moderation.
        </p>
      </Section>

      <Section title="Disclaimer">
        <p className="text-gray-500 italic">
          Authority mappings are based on available geographic data and are not guaranteed to
          be 100% accurate. The platform uses the term "likely authority" intentionally — the
          actual responsible authority may differ. This platform is not affiliated with any
          government agency.
        </p>
      </Section>

      <div className="mt-10 pt-6 border-t text-center">
        <p className="text-sm text-gray-500 mb-4">
          Have feedback or questions? We'd love to hear from you.
        </p>
        <Link
          to="/report"
          className="inline-flex items-center justify-center px-6 py-2 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 transition-colors"
        >
          Report an issue now
        </Link>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-8">
      <h2 className="text-xl font-semibold text-gray-800 mb-3">{title}</h2>
      <div className="text-gray-600 leading-relaxed">{children}</div>
    </div>
  );
}
