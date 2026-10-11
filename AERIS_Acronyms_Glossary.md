# AERIS — System Acronyms & Terminology Glossary

Comprehensive technical, atmospheric, and cloud computing glossary for the **AERIS (Atmospheric Emission-Response Intelligence System)** project, published for Bharat Builds 2026 and AWS Builder Center.

---

## 1. Core System & Project Architecture

| Acronym | Full Form | Definition & Context in AERIS |
| :--- | :--- | :--- |
| **AERIS** | **A**tmospheric **E**mission-**R**esponse **I**ntelligence **S**ystem | The end-to-end open-source physical control plane and 72-hour forecasting platform. |
| **SAMEER** | System for Air Quality Management & Evaluation in Real time | Central Pollution Control Board (CPCB) official consumer portal providing live National AQI across India. |

---

## 2. Atmospheric Science & Environmental Meteorology

| Acronym | Full Form | Definition & Context in AERIS |
| :--- | :--- | :--- |
| **AQI** | **A**ir **Q**uality **I**ndex | Unitless composite metric (0–500) categorizing ambient air safety from Good to Severe. |
| **NAQI** | **N**ational **A**ir **Q**uality **I**ndex | India's statutory 8-pollutant air quality index standard developed by IIT Kanpur and CPCB. |
| **PM2.5** | **P**articulate **M**atter $\le 2.5 \mu\text{m}$ | Fine respirable combustion particles that penetrate deep into lung alveolar tissue. |
| **PM10** | **P**articulate **M**atter $\le 10 \mu\text{m}$ | Coarse inhalable dust and mechanical road dust particles. |
| **PBL / PBLH**| **P**lanetary **B**oundary **L**ayer (Height) | The lowest tropospheric layer directly affected by earth surface heating. Nocturnal collapse caps pollutants. |
| **NO2** | **N**itrogen **D**ioxide | Combustion byproduct from diesel engines and thermal power generation; photochemical ozone precursor. |
| **O3** | Ground-Level **O**zone | Secondary pollutant formed via photochemical oxidation of VOCs and NOx under solar radiation. |
| **FRP** | **F**ire **R**adiative **P**ower | Satellite measurement of radiant heat energy emitted by biomass/stubble fires, measured in MegaWatts (MW). |
| **NASA FIRMS**| **F**ire **I**nformation for **R**esource **M**anagement **S**ystem | NASA satellite portal distributing near-real-time active thermal fire hotspot pixels. |
| **MODIS** | **M**oderate Resolution **I**maging **S**pectroradiometer | NASA Earth Observing System sensor aboard the Terra and Aqua satellites detecting crop fires. |
| **VIIRS** | **V**isible **I**nfrared **I**maging **R**adiometer **S**uite | High-resolution 375m sensor aboard Suomi NPP and NOAA-20 satellites tracking localized thermal hotspots. |
| **WRF-Chem** | **W**eather **R**esearch and **F**orecasting coupled with **Chem**istry | State-of-the-art non-hydrostatic numerical weather and chemical transport model. |
| **ECMWF** | **E**uropean **C**entre for **M**edium-Range **W**eather **F**orecasts | Global meteorological research center providing reanalysis and operational weather data. |
| **ERA5** | **E**CMWF **R**e**a**nalysis version **5** | High-resolution global atmospheric reanalysis combining model physics with historical observations. |
| **CAMS** | **C**opernicus **A**tmosphere **M**onitoring **S**ervice | EU Copernicus operational data service providing global chemical composition and aerosol optical depth. |
| **GFAS** | **G**lobal **F**ire **A**ssimilation **S**ystem | CAMS daily biomass burning emissions inventory calculated from satellite Fire Radiative Power. |
| **CPCB** | **C**entral **P**ollution **C**ontrol **B**oard | India's national statutory authority governing water and air environmental standards. |
| **DPCC** | **D**elhi **P**ollution **C**ontrol **C**ommittee | State environmental protection agency managing continuous air monitoring stations in Delhi. |
| **NAAQS** | **N**ational **A**mbient **A**ir **Q**uality **S**tandards | Indian regulatory thresholds (e.g., 24-hour PM2.5 limit of $60\,\mu\text{g/m}^3$, PM10 limit of $100\,\mu\text{g/m}^3$). |

---

## 3. Mathematics, Dynamical Systems & Machine Learning

| Acronym | Full Form | Definition & Context in AERIS |
| :--- | :--- | :--- |
| **MPC** | **M**odel **P**redictive **C**ontrol | Optimization framework calculating optimal time-series intervention schedules (e.g., anti-smog misting). |
| **DMD** | **D**ynamic **M**ode **D**ecomposition | Data-driven algorithm extracting dominant spatiotemporal coherent modes from complex fluid flows. |
| **DMDc** | Dynamic Mode Decomposition with **C**ontrol | Extended DMD formulation mapping exogenous policy inputs (mist cannons, truck bans) to state trajectories. |
| **Koopman** | Koopman Operator Theory | Infinite-dimensional linear transformation representing nonlinear chaotic fluid dynamics in Hilbert space. |
| **Lyapunov** | Lyapunov Stability & Covariance | Analytical mathematical error propagation framework bounding forecast uncertainty envelopes over 72 hours. |
| **SLSQP** | **S**equential **L**east **Sq**uares **P**rogramming | Numerical optimization solver in SciPy used by AERIS for constrained nonlinear municipal control. |
| **RMSE** | **R**oot **M**ean **S**quare **E**rror | Primary accuracy metric evaluating AERIS forward rollouts against held-out observations ($14.8\,\mu\text{g/m}^3$). |
| **CI** | **C**onfidence **I**nterval | Statistical certainty bound (e.g., $\pm 1.96\sigma$, 95% Confidence Interval on rollout plots). |
| **PDE** | **P**artial **D**ifferential **E**quation | Numerical mathematical formulation governing continuous fluid transport (e.g., Navier-Stokes advection-diffusion). |

---

## 4. Cloud Computing & AWS Open-Source Tooling

| Acronym | Full Form | Definition & Context in AERIS |
| :--- | :--- | :--- |
| **AWS** | **A**mazon **W**eb **S**ervices | Cloud computing platform whose open-source tools power AERIS for ₹0 cloud spend. |
| **SAM** | **S**erverless **A**pplication **M**odel | AWS framework and CLI used to run Lambda serverless functions locally on laptops via `sam local start-api`. |
| **SDK** | **S**oftware **D**evelopment **K**it | Developer libraries (e.g., Strands Agents SDK used for multi-agent reasoning). |
| **SNS** | Amazon **S**imple **N**otification **S**ervice | Fully managed pub/sub messaging engine dispatching emergency SMS and push warnings to registered phones. |
| **SES** | Amazon **S**imple **E**mail **S**ervice | Cloud-based email sending service transmitting verified school and citizen air hazard warnings. |
| **S3** | Amazon **S**imple **S**torage **S**ervice | Object storage engine storing processed grid arrays and static dashboard assets. |
| **CDN** | **C**ontent **D**elivery **N**etwork | Distributed global edge caching service (Amazon CloudFront) delivering instant telemetry. |
| **Cedar** | AWS Cedar Policy Language | Open-source declarative policy engine providing formal mathematical authorization for statutory GRAP actions. |
| **OpenSearch**| Amazon OpenSearch | Open-source distributed search engine executing geospatial bounding box hotspot searches in $<5\,\text{ms}$. |
| **LocalStack** | LocalStack Cloud Emulator | Offline cloud mockup framework running emulated DynamoDB, S3, and SNS on `localhost:4566`. |
| **Finch** | Finch Container Runtime | Open-source CLI tool for container isolation and lightweight microVM execution. |

---

## 5. Governance, Legal & Statutory Frameworks

| Acronym | Full Form | Definition & Context in AERIS |
| :--- | :--- | :--- |
| **CAQM** | **C**ommission for **A**ir **Q**uality **M**anagement | Statutory body established under the CAQM Act, 2021 with legal power over Delhi NCR and adjoining states. |
| **GRAP** | **G**raded **R**esponse **A**ction **P**lan | Tiered emergency environmental protocol triggered automatically when pollution crosses statutory thresholds. |
| **GRAP-IV** | GRAP Stage **IV** (Emergency / Severe+) | Highest emergency stage (AQI $>450$), ordering school closures, truck entry bans, and construction halts. |
| **NCR** | **N**ational **C**apital **R**egion | Inter-state metropolitan region covering Delhi and bordering districts in Haryana, UP, and Rajasthan. |

---

## 6. Software Architecture & Network Protocols

| Acronym | Full Form | Definition & Context in AERIS |
| :--- | :--- | :--- |
| **API** | **A**pplication **P**rogramming **I**nterface | Standardized software interface connecting the dashboard to backend forecasting engines. |
| **REST** | **Re**presentational **S**tate **T**ransfer | Stateless architectural style used by FastAPI for HTTP endpoints. |
| **SMTP** | **S**imple **M**ail **T**ransfer **P**rotocol | Internet standard protocol used to deliver emergency alert advisories directly to inboxes. |
| **SPA** | **S**ingle **P**age **A**pplication | Modern web client architecture loading a single HTML page and dynamically updating content via JavaScript. |
| **PWA** | **P**rogressive **W**eb **A**pp | Web application designed with mobile app behaviors, installability, and responsive layouts. |
| **QR Code** | **Q**uick **R**esponse Code | 2D matrix barcode scanned from smartphones for dynamic Wi-Fi network onboarding and alert registration. |
| **SVG** | **S**calable **V**ector **G**raphics | XML-based vector image format used for interactive advection timeline and dynamic trajectory charts. |
| **CSP** | **C**ontent **S**ecurity **P**olicy | Web security layer restricting which dynamic resources and images can be loaded by web browsers. |
| **OSS** | **O**pen **S**ource **S**oftware | Software with publicly accessible source code allowing free inspection, modification, and reproduction. |

---

*Compiled for the AERIS Project — Bharat Builds 2026.*
