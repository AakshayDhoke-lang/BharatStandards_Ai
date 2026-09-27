export type QuickTestCase = {
  id: string;
  category: "Electrical" | "Mechanical" | "Civil" | "Medical";
  title: string;
  description: string;
};

export const QUICK_TEST_CASES: QuickTestCase[] = [
  {
    id: "electrical-ceiling-fan",
    category: "Electrical",
    title: "Ceiling Fan",
    description:
      "Supply of 500 ceiling fans for government school classrooms. Fans shall operate on 230 V AC, 50 Hz supply with a minimum sweep of 1200 mm. Electrical safety, performance testing and applicable BIS certification requirements shall be considered.",
  },
  {
    id: "mechanical-centrifugal-pump",
    category: "Mechanical",
    title: "Centrifugal Water Pump",
    description:
      "Supply of centrifugal water pumps for municipal water circulation. Pumps shall be suitable for continuous operation, designed for clean water service and supplied with required performance, pressure, efficiency, material and testing specifications.",
  },
  {
    id: "civil-structural-steel",
    category: "Civil",
    title: "Structural Steel",
    description:
      "Procurement of structural steel for construction of a government building. Steel shall be suitable for load-bearing structural members and shall meet applicable requirements for material grade, mechanical properties, chemical composition, dimensional tolerances, testing and quality certification.",
  },
  {
    id: "medical-examination-gloves",
    category: "Medical",
    title: "Surgical Examination Gloves",
    description:
      "Procurement of disposable medical examination gloves for use in government healthcare facilities. Gloves shall provide suitable barrier protection and meet applicable requirements for material quality, dimensions, physical performance, safety, testing, packaging and marking.",
  },
];
