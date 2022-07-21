FROM gradle:7.4.2-jdk17-alpine AS build

WORKDIR /home/gradle/src/

COPY build.gradle .
COPY settings.gradle .

RUN gradle downloadDependencies --no-daemon

COPY . .

RUN gradle assemble installDist --no-daemon

FROM amazoncorretto:17-alpine3.15

COPY --from=build /home/gradle/src/build/install/progphil-bot/ .

ENTRYPOINT ["sh", "bin/progphil-bot"]